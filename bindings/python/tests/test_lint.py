import os
import subprocess
import sys
from pathlib import Path

import pytest
from gdp.lint import check_file


@pytest.mark.parametrize(
    "source,expected",
    [
        ("from gdp import define_proof as make\n_issuer = make('Admin')\n", {"GDP001"}),
        ("import gdp as g\n_issuer = g.define_proof('Admin')\n", {"GDP001"}),
        ("import gdp._gdp as core\n_issuer = core.define_proof('Admin')\n", {"GDP001"}),
        ("import gdp._gdp\n_issuer = gdp._gdp.define_proof('Admin')\n", {"GDP001"}),
        ("from gdp import Proof\nproof = Proof()\n", {"GDP004"}),
        ("from gdp import Proof\nproof = Proof[str]()\n", {"GDP004"}),
        ("proof = issuer.prove(user, project)\n", {"GDP003"}),
        (
            "from gdp import Proof as P\nfrom typing import cast\nx = cast(P, {})\n",
            {"GDP005"},
        ),
        (
            "from gdp import Proof as P\nfrom typing import cast as convert\n"
            "x = convert(P[str], {})\n",
            {"GDP005"},
        ),
        ("from proofs.admin import _issuer\n", {"GDP006"}),
        ("from proofs.admin import *\n", {"GDP006"}),
        ("protected.__wrapped__(project, proof=None)\n", {"GDP007"}),
        ("bypass = protected.__wrapped__\n", {"GDP007"}),
        (
            "from inspect import unwrap as original\noriginal(protected)(project)\n",
            {"GDP007"},
        ),
        ("import inspect as i\ni.unwrap(protected)\n", {"GDP007"}),
    ],
)
def test_lint_command_rejects_boundary_violations(tmp_path, source, expected):
    module = tmp_path / "handler.py"
    module.write_text(source)
    diagnostics = check_file(module)
    assert {diagnostic.code for diagnostic in diagnostics} == expected
    result = subprocess.run(
        [sys.executable, "-m", "gdp.lint", str(module)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert all(code in result.stdout for code in expected)


def test_private_trusted_module_passes_and_exported_issuer_fails(tmp_path):
    trusted = tmp_path / "proofs"
    trusted.mkdir()
    module = trusted / "admin.py"
    module.write_text(
        "from gdp import define_proof\n"
        "_issuer = define_proof('Admin')\n"
        "Admin = _issuer.kind\n"
        "def check(user, project):\n"
        "    return _issuer.prove(user, project)\n"
    )
    assert check_file(module) == []
    for export in (
        "issuer = _issuer\n",
        "__all__ = ['_issuer']\n",
        "def leak():\n    return _issuer\n",
    ):
        module.write_text(module.read_text().split("def check")[0] + export)
        assert "GDP006" in {item.code for item in check_file(module)}
    module.write_text("from gdp import define_proof\nissuer = define_proof('Admin')\n")
    assert {item.code for item in check_file(module)} == {"GDP002"}


def test_relative_private_issuer_imports_are_rejected(tmp_path):
    package = tmp_path / "app"
    trusted = package / "proofs"
    trusted.mkdir(parents=True)
    for source in ("from .admin import _issuer\n", "from . import _issuer\n"):
        module = trusted / "checks.py"
        module.write_text(source)
        assert {item.code for item in check_file(module)} == {"GDP006"}
    nested = trusted / "nested"
    nested.mkdir()
    module = nested / "checks.py"
    module.write_text("from ..admin import _issuer\n")
    assert {item.code for item in check_file(module)} == {"GDP006"}
    module = package / "handler.py"
    module.write_text("from .proofs.admin import _issuer\n")
    assert {item.code for item in check_file(module)} == {"GDP006"}
    module.write_text("from .helpers import _helper\n")
    assert check_file(module) == []
    module.write_text("obj.unwrap(callback)\n")
    assert check_file(module) == []


def test_packaged_examples_pass_lint_and_bad_input_fails_closed():
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "-m", "gdp.lint", str(root / "examples/python")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    result = subprocess.run(
        [sys.executable, "-m", "gdp.lint", str(root / "missing.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "GDP000" in result.stderr


def test_explicit_source_under_hidden_ancestor_is_checked(tmp_path):
    folder = tmp_path / ".app"
    folder.mkdir()
    source = folder / "handler.py"
    source.write_text("from gdp import define_proof\n_issuer = define_proof('Admin')\n")
    for target in (source, folder):
        result = subprocess.run(
            [sys.executable, "-m", "gdp.lint", str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "GDP001" in result.stdout


def test_directory_scan_preserves_explicit_inputs_and_sorted_diagnostics(tmp_path):
    for folder in (".git", ".venv", "__pycache__", "node_modules", ".test-wheel"):
        ignored = tmp_path / folder / "nested"
        ignored.mkdir(parents=True)
        (ignored / "bad.py").write_text("protected.__wrapped__()\n")
    for relative in ("z.py", "app/a.py", ".app/b.py"):
        source = tmp_path / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("protected.__wrapped__()\n")
    (tmp_path / "package.py").mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "gdp.lint", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        f"{tmp_path / '.app/b.py'}:1: GDP007 Do not bypass protected callable wrappers",
        f"{tmp_path / 'app/a.py'}:1: GDP007 Do not bypass protected callable wrappers",
        f"{tmp_path / 'package.py'}:1: GDP000 Cannot read Python source",
        f"{tmp_path / 'z.py'}:1: GDP007 Do not bypass protected callable wrappers",
    ]
    result = subprocess.run(
        [sys.executable, "-m", "gdp.lint", str(tmp_path / ".venv/nested/bad.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "GDP007" in result.stdout


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason="Requires POSIX directory permissions and an unprivileged user",
)
def test_unreadable_directories_fail_the_lint_command(tmp_path):
    child = tmp_path / "app"
    child.mkdir()
    (child / "handler.py").write_text("protected.__wrapped__()\n")
    readable = subprocess.run(
        [sys.executable, "-m", "gdp.lint", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert readable.returncode == 1
    assert "GDP007" in readable.stdout
    child.chmod(0)
    try:
        for target in (tmp_path, child):
            result = subprocess.run(
                [sys.executable, "-m", "gdp.lint", str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 1
            assert "GDP000" in result.stdout + result.stderr
            assert str(child) in result.stdout + result.stderr
    finally:
        child.chmod(0o700)
