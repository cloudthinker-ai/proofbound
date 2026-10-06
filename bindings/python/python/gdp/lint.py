from __future__ import annotations

import argparse
import ast
import os
import sys
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Diagnostic:
    path: Path
    line: int
    code: str
    message: str


class _Checker(ast.NodeVisitor):
    def __init__(self, path: Path, tree: ast.Module) -> None:
        self.path = path
        self.trusted = "proofs" in path.parts
        self.aliases: dict[str, str] = {}
        self.issuers: set[str] = set()
        self.diagnostics: list[Diagnostic] = []
        self.tree = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in ("gdp", "gdp._gdp"):
                for alias in node.names:
                    self.aliases[alias.asname or alias.name] = f"gdp.{alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module in (
                "typing",
                "inspect",
            ):
                for alias in node.names:
                    self.aliases[alias.asname or alias.name] = (
                        f"{node.module}.{alias.name}"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ("gdp", "gdp._gdp"):
                        self.aliases[alias.asname or "gdp"] = "gdp"
                    elif alias.name in ("typing", "inspect"):
                        self.aliases[alias.asname or alias.name] = alias.name
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                if (
                    isinstance(value, ast.Call)
                    and self._resolve(value.func) == "gdp.define_proof"
                ):
                    targets = (
                        node.targets if isinstance(node, ast.Assign) else [node.target]
                    )
                    for target in targets:
                        if isinstance(target, ast.Name):
                            self.issuers.add(target.id)

    @cached_property
    def parents(self) -> dict[ast.AST, ast.AST]:
        return {
            child: parent
            for parent in ast.walk(self.tree)
            for child in ast.iter_child_nodes(parent)
        }

    def _resolve(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return self.aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            name = f"{self._resolve(node.value)}.{node.attr}"
            return "gdp" if name == "gdp._gdp" else name
        if isinstance(node, ast.Subscript):
            return self._resolve(node.value)
        return ""

    def _report(self, node: ast.AST, code: str, message: str) -> None:
        self.diagnostics.append(
            Diagnostic(self.path, getattr(node, "lineno", 1), code, message)
        )

    def visit_Call(self, node: ast.Call) -> None:
        function = self._resolve(node.func)
        if function == "inspect.unwrap":
            self._report(node, "GDP007", "Do not unwrap protected callables")
        if function == "gdp.define_proof":
            if not self.trusted:
                self._report(
                    node, "GDP001", "Define proof issuers only in proofs/ modules"
                )
            parent = self.parents.get(node)
            targets = (
                parent.targets
                if isinstance(parent, ast.Assign)
                else [parent.target]
                if isinstance(parent, ast.AnnAssign)
                else []
            )
            if (
                len(targets) != 1
                or not isinstance(targets[0], ast.Name)
                or not targets[0].id.startswith("_")
                or parent is None
                or not isinstance(self.parents.get(parent), ast.Module)
            ):
                self._report(
                    node,
                    "GDP002",
                    "Keep each issuer in a private module-level variable",
                )
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "prove"
            and not self.trusted
        ):
            self._report(node, "GDP003", "Mint proofs only in proofs/ modules")
        if function in (
            "gdp.Proof",
            "gdp.Named",
            "gdp.Prover",
            "gdp.ProofKind",
            "gdp.Names",
        ):
            self._report(
                node, "GDP004", "Opaque GDP objects cannot be constructed directly"
            )
        if function in ("cast", "typing.cast") and node.args:
            target = (
                self._resolve(node.args[0].value)
                if isinstance(node.args[0], ast.Subscript)
                else self._resolve(node.args[0])
            )
            if target in ("gdp.Proof", "gdp.Named", "gdp.Prover", "gdp.ProofKind"):
                self._report(
                    node, "GDP005", "Do not cast values into proof or authority types"
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "__wrapped__":
            self._report(node, "GDP007", "Do not bypass protected callable wrappers")
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        if isinstance(node.value, ast.Name) and node.value.id in self.issuers:
            self._report(node, "GDP006", "Return proofs or verifiers, never the issuer")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self._check_export(node, node.targets, node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._check_export(node, [node.target], node.value)
        self.generic_visit(node)

    def _check_export(
        self, node: ast.AST, targets: list[ast.expr], value: ast.expr | None
    ) -> None:
        if isinstance(value, ast.Name) and value.id in self.issuers:
            for target in targets:
                if not isinstance(target, ast.Name) or not target.id.startswith("_"):
                    self._report(node, "GDP006", "Do not export a proof issuer")
        if any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in targets
        ):
            for item in ast.walk(value) if value else ():
                if isinstance(item, ast.Constant) and item.value in self.issuers:
                    self._report(node, "GDP006", "Do not include an issuer in __all__")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module_parts = (node.module or "").split(".")
        if node.level:
            package = self.path.parent
            for _ in range(node.level - 1):
                package = package.parent
            module_parts = [*package.parts, *module_parts]
        if "proofs" in module_parts:
            for alias in node.names:
                if alias.name.startswith("_") or alias.name == "*":
                    self._report(
                        node,
                        "GDP006",
                        "Import public checkers and verifiers, never private issuers",
                    )
        self.generic_visit(node)


def check_file(path: Path) -> list[Diagnostic]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeError):
        return [Diagnostic(path, 1, "GDP000", "Cannot parse Python source")]
    checker = _Checker(path, tree)
    checker.visit(tree)
    return sorted(checker.diagnostics, key=lambda item: (item.line, item.code))


def _ignored(name: str) -> bool:
    return name in (".git", ".venv", "__pycache__", "node_modules") or name.startswith(
        ".test-"
    )


def _sources(path: Path) -> tuple[list[Path], list[Diagnostic]]:
    if not path.is_dir():
        return [path], []
    files: list[Path] = []
    diagnostics: list[Diagnostic] = []

    def unreadable(error: OSError) -> None:
        diagnostics.append(
            Diagnostic(
                Path(error.filename) if error.filename else path,
                1,
                "GDP000",
                "Cannot read Python source directory",
            )
        )

    for directory, folders, entries in os.walk(path, onerror=unreadable):
        folders[:] = [folder for folder in folders if not _ignored(folder)]
        files.extend(
            Path(directory) / entry
            for entry in (*folders, *entries)
            if not _ignored(entry) and Path(entry).match("*.py")
        )
    return sorted(files), diagnostics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check GDP trusted-module boundaries")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failures = 0
    for path in args.paths:
        if not path.exists():
            print(f"{path}:1: GDP000 Input path does not exist", file=sys.stderr)
            failures += 1
            continue
        sources, diagnostics = _sources(path)
        for source in sources:
            try:
                diagnostics.extend(check_file(source))
            except OSError:
                diagnostics.append(
                    Diagnostic(source, 1, "GDP000", "Cannot read Python source")
                )
        for diagnostic in diagnostics:
            print(
                f"{diagnostic.path}:{diagnostic.line}: "
                f"{diagnostic.code} {diagnostic.message}"
            )
        failures += len(diagnostics)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
