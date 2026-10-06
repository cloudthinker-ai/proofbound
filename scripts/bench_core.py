import argparse
import json
import math
import os
import platform
import statistics
import subprocess
import tempfile
from pathlib import Path

CASES = (
    "baseline",
    "name1",
    "name2",
    "name3",
    "prove0",
    "prove1",
    "prove2",
    "prove3",
    "typed_prove2",
    "runtime_require2",
    "typed_require2",
    "typed_flow2",
    "runtime_scope_flow2",
)
UPSTREAM_REVISION = "ebd0af9cae423997a43a024dc6d6738b0895bbec"


def expected(case: str, iterations: int) -> int:
    def value(index: int) -> int:
        base = index & 1023
        if "prove" in case:
            return base ^ 9
        if "require" in case:
            return base ^ 7
        if case == "name3":
            return base + 59
        if case == "name2" or "flow" in case:
            return base + 17
        return base

    cycles, rest = divmod(iterations, 1024)
    return (
        cycles * sum(value(index) for index in range(1024))
        + sum(value(index) for index in range(rest))
    ) & 0xFFFFFFFF


def command(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def sample(arguments: list[str], expected_checksum: int) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="proofbound-core-time-") as directory:
        usage_path = Path(directory) / "usage.json"
        result = subprocess.run(
            [
                "/usr/bin/time",
                "-f",
                '{"peak_rss_kib":%M,"process_wall_s":%e,"process_user_s":%U,"process_system_s":%S}',
                "-o",
                str(usage_path),
                *arguments,
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        if result.stderr:
            raise RuntimeError(result.stderr)
        measured = json.loads(result.stdout)
        if measured["checksum"] != expected_checksum:
            raise AssertionError("Core benchmark output differs from checksum oracle")
        measured.update(json.loads(usage_path.read_text()))
        return measured


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare shipped Rust and gdp-ts core designs"
    )
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument(
        "--rust", type=Path, default=Path("target/release/examples/bench_core")
    )
    parser.add_argument("--iterations", type=int, default=1000000)
    parser.add_argument("--samples", type=int, default=9)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.samples < 2 or args.repetitions < 1 or args.iterations < 1:
        parser.error("Use positive iterations/repetitions and at least two samples")
    if (
        command("git", "-C", str(args.upstream), "rev-parse", "HEAD")
        != UPSTREAM_REVISION
    ):
        raise ValueError("Upstream checkout differs from the pinned source revision")
    affinity = os.sched_getaffinity(0)
    cpu = min(affinity)
    os.sched_setaffinity(0, {cpu})
    args.output.mkdir(parents=True, exist_ok=True)
    report = {
        "platform": platform.platform(),
        "cpu": command("lscpu"),
        "node": command("node", "--version"),
        "rust": command("rustc", "--version"),
        "proofbound_revision": command("git", "rev-parse", "HEAD"),
        "upstream_revision": UPSTREAM_REVISION,
        "iterations": args.iterations,
        "samples": args.samples,
        "warmups_per_process": 2,
        "cpu_affinity": [cpu],
        "available_cpus_before_pin": len(affinity),
        "initial_load": os.getloadavg(),
        "repetitions": [],
    }
    for repetition in range(args.repetitions):
        rows = {}
        for case in CASES:
            checksum = expected(case, args.iterations)
            commands = {
                "proofbound": [str(args.rust.resolve()), case, str(args.iterations)],
                "gdp_ts": [
                    "node",
                    "scripts/bench_upstream.mjs",
                    str((args.upstream / "src/index.ts").resolve()),
                    case,
                    str(args.iterations),
                ],
            }
            raw: dict[str, list[dict[str, object]]] = {name: [] for name in commands}
            for index in range(args.samples):
                order = list(commands)
                if (index + repetition) % 2:
                    order.reverse()
                for name in order:
                    raw[name].append(sample(commands[name], checksum))
            summary = {}
            for name, entries in raw.items():
                metrics = {}
                for metric in ("wall_ns", "cpu_ns", "peak_rss_kib"):
                    values = sorted(entry[metric] for entry in entries)
                    divisor = args.iterations if metric.endswith("_ns") else 1
                    metrics[metric + "_median"] = statistics.median(values) / divisor
                    metrics[metric + "_p95"] = (
                        values[math.ceil(len(values) * 0.95) - 1] / divisor
                    )
                summary[name] = metrics
            rows[case] = {"summary": summary, "samples": raw, "checksum": checksum}
            print(
                f"run {repetition + 1} {case:22} "
                f"Rust {summary['proofbound']['wall_ns_median']:9.2f} ns/op  "
                f"gdp-ts {summary['gdp_ts']['wall_ns_median']:9.2f} ns/op",
                flush=True,
            )
        report["repetitions"].append({"results": rows, "load_average": os.getloadavg()})
        (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    report["checksum_parity"] = "PASS"
    report["guarantee_equivalence"] = False
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print("CHECKSUM PARITY: PASS; runtime guarantees differ")


if __name__ == "__main__":
    main()
