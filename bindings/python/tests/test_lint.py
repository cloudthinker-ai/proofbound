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
        ("from gdp import Proof\nproof = Proof()\n", {"GDP004"}),
        ("proof = issuer.prove(user, project)\n", {"GDP003"}),
        (
            "from gdp import Proof as P\nfrom typing import cast\nx = cast(P, {})\n",
            {"GDP005"},
        ),
        ("from proofs.admin import _issuer\n", {"GDP006"}),
        ("from proofs.admin import *\n", {"GDP006"}),
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
