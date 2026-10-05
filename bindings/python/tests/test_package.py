import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

import gdp
from gdp import _gdp


def test_installed_extension_matches_public_stub():
    stub = Path(gdp.__file__).parent / "_gdp.pyi"
    tree = ast.parse(stub.read_text())
    declared = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef))
    } | {
        node.target.id
        for node in tree.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    assert declared - {"__all__"} == set(_gdp.__all__)
    assert _gdp.INTERFACE_VERSION == 1
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name == "AuthorizationError":
            continue
        methods = {
            method.name
            for method in node.body
            if isinstance(method, ast.FunctionDef) and not method.name.startswith("_")
        }
        actual = {
            name for name in dir(getattr(_gdp, node.name)) if not name.startswith("_")
        }
        assert methods == actual, node.name
    assert inspect.signature(gdp.define_proof).parameters.keys() == {"kind", "tag"}


def test_incompatible_interface_is_rejected_at_import():
    program = (
        "import importlib, gdp\n"
        "gdp._gdp.INTERFACE_VERSION = 999\n"
        "try:\n"
        "    importlib.reload(gdp)\n"
        "except ImportError:\n"
        "    print('rejected')\n"
        "else:\n"
        "    raise AssertionError('incompatible wheel accepted')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "rejected"
    assert importlib.reload(gdp).name("healthy").value == "healthy"
