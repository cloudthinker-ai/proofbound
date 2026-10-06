import argparse
import asyncio
import gc
import importlib.util
import io
import json
import math
import os
import platform
import statistics
import sys
import tempfile
import time
from collections.abc import Callable
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType

import gdp
import gdp.lint


def load_baseline(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "_proofbound_baseline", path / "__init__.py"
    )
    if spec is None or spec.loader is None:
        raise ValueError("Baseline must be an installed gdp package directory")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    lint_spec = importlib.util.spec_from_file_location(
        spec.name + ".lint", path / "lint.py"
    )
    if lint_spec is None or lint_spec.loader is None:
        raise ValueError("Baseline lint module is missing")
    module.lint = importlib.util.module_from_spec(lint_spec)
    sys.modules[lint_spec.name] = module.lint
    lint_spec.loader.exec_module(module.lint)
    return module


def cases(
    module: ModuleType, source: Path, tree: Path
) -> dict[str, Callable[[], object]]:
    issuer = module.define_proof("Benchmark")
    kind = issuer.kind
    user, project = module.name("alice"), module.name("p1")
    proof = issuer.prove(user, project)
    plan = issuer.prove(project)
    requirement = module.Requirement(kind, ("user", "project"))

    @module.requires(proof=requirement)
    def positional(user, project, proof):
        return project.value

    @module.requires(proof=requirement)
    def keywords(user, project, *, proof):
        return project.value

    @module.requires(proof=requirement)
    def defaults(user=user, project=project, *, proof=proof):
        return project.value

    @module.requires(proof=requirement, plan=module.Requirement(kind, ("project",)))
    def multiple(user, project, *, proof, plan):
        return project.value

    @module.requires(proof=requirement)
    def variadic(user, project, *extra, proof, **options):
        return project.value

    @module.requires(proof=requirement)
    async def asynchronous(user, project, *, proof):
        return project.value

    def scoped():
        with module.names("alice", "p1") as subjects:
            kind.require(issuer.prove(*subjects), *subjects)
            return subjects[1].value

    def rejected():
        try:
            keywords(project, user, proof=proof)
        except module.AuthorizationError:
            return "rejected"
        raise AssertionError("Wrong subjects were accepted")

    async def async_batch():
        for _ in range(100):
            result = await asynchronous(user, project, proof=proof)
        return result

    def lint():
        return [
            (item.line, item.code, item.message)
            for item in module.lint.check_file(source)
        ]

    def lint_tree():
        with redirect_stdout(io.StringIO()) as output:
            status = module.lint.main([str(tree)])
        return status, output.getvalue()

    result: dict[str, Callable[[], object]] = {
        "protected_positional": lambda: positional(user, project, proof),
        "protected_keywords": lambda: keywords(user, project, proof=proof),
        "protected_all_keywords": lambda: keywords(
            user=user, project=project, proof=proof
        ),
        "protected_defaults": defaults,
        "protected_two_proofs": lambda: multiple(user, project, proof=proof, plan=plan),
        "protected_variadic": lambda: variadic(
            user, project, 1, 2, proof=proof, option=3
        ),
        "protected_async_100": lambda: asyncio.run(async_batch()),
        "rejected_subjects": rejected,
        "scope_issue_verify": scoped,
        "lint_500_lines": lint,
        "lint_tree_1000_ignored": lint_tree,
    }
    for count in (0, 1, 2, 8, 64):
        subjects = tuple(module.name(index) for index in range(count))
        authority = issuer.prove(*subjects)
        result[f"require_{count}"] = lambda subjects=subjects, authority=authority: (
            kind.require(authority, *subjects)
        )
    return result


def measure(function: Callable[[], object], iterations: int) -> dict[str, float]:
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        wall = time.perf_counter_ns()
        cpu = time.process_time_ns()
        for _ in range(iterations):
            function()
        cpu = time.process_time_ns() - cpu
        wall = time.perf_counter_ns() - wall
    finally:
        if was_enabled:
            gc.enable()
    return {"cpu_ns": cpu / iterations, "wall_ns": wall / iterations}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Paired release-build Python benchmarks"
    )
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--iterations", type=int, default=10000)
    parser.add_argument("--samples", type=int, default=9)
    args = parser.parse_args()
    if args.samples < 2 or args.iterations < 1:
        parser.error("Use at least two samples and one iteration")
    variants = {"current": gdp}
    if args.baseline:
        variants = {"baseline": load_baseline(args.baseline), **variants}
    report: dict[str, object] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "samples": args.samples,
        "iterations": args.iterations,
        "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        "cpu_affinity": sorted(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else None,
        "results": {},
    }
    with tempfile.TemporaryDirectory(prefix="proofbound-bench-") as directory:
        source = Path(directory) / "handler.py"
        source.write_text(
            "\n".join(f"value_{index} = {index}" for index in range(500))
            + "\nprotected.__wrapped__()\nissuer.prove(subject)\n",
            encoding="utf-8",
        )
        tree = Path(directory) / "tree"
        tree.mkdir()
        for index in range(16):
            (tree / f"handler_{index}.py").write_text(
                "protected.__wrapped__()\n", encoding="utf-8"
            )
        for index in range(100):
            ignored = tree / ".venv" / str(index)
            ignored.mkdir(parents=True)
            for leaf in range(10):
                (ignored / f"dependency_{leaf}.py").write_text(
                    "protected.__wrapped__()\n", encoding="utf-8"
                )
        functions = {
            name: cases(module, source, tree) for name, module in variants.items()
        }
        rows = {}
        for case in functions["current"]:
            expected = functions["current"][case]()
            for entries in functions.values():
                if entries[case]() != expected:
                    raise AssertionError(f"Output mismatch: {case}")
            iterations = args.iterations
            if case.startswith("lint_"):
                iterations = max(1, iterations // 1000)
            elif case == "protected_async_100":
                iterations = max(1, iterations // 100)
            for entries in functions.values():
                for _ in range(2):
                    measure(entries[case], iterations)
            raw: dict[str, list[dict[str, float]]] = {name: [] for name in variants}
            for sample in range(args.samples):
                order = list(variants)
                if sample % 2:
                    order.reverse()
                for name in order:
                    raw[name].append(measure(functions[name][case], iterations))
            summaries = {}
            for name, samples in raw.items():
                summary = {}
                for metric in ("cpu_ns", "wall_ns"):
                    values = sorted(sample[metric] for sample in samples)
                    summary[f"{metric}_median"] = statistics.median(values)
                    summary[f"{metric}_p95"] = values[math.ceil(len(values) * 0.95) - 1]
                summaries[name] = summary
            rows[case] = {"summary": summaries, "samples": raw}
            current = summaries["current"]["cpu_ns_median"]
            ratio = (
                summaries["baseline"]["cpu_ns_median"] / current
                if "baseline" in summaries
                else 1
            )
            print(f"{case:26} {current / 1000:10.3f} us CPU  {ratio:6.2f}x", flush=True)
        report["results"] = rows
    report["parity"] = "PASS"
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PARITY: PASS")


if __name__ == "__main__":
    main()
