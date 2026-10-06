import subprocess
import sys

import pytest


@pytest.mark.parametrize("checker", ["mypy", "pyrefly"])
def test_installed_types_reject_wrong_kinds_missing_proofs_and_scoped_types(
    tmp_path, checker
):
    valid = tmp_path / "valid.py"
    valid.write_text(
        "from typing import assert_type\n"
        "from typing import Any\n"
        "from gdp import (Named, Names, Proof, Requirement, define_proof,\n"
        "    name, names, requires)\n"
        "class Admin: pass\n"
        "class Plan: pass\n"
        "admin = define_proof('Admin', tag=Admin)\n"
        "plan = define_proof('Plan', tag=Plan)\n"
        "@requires(proof=Requirement(admin.kind, ('project',)))\n"
        "def write(project: Named[str], proof: Proof[Admin]) -> str:\n"
        "    return project.value\n"
        "project = name('project')\n"
        "write(project, admin.prove(project))\n"
        "with names() as empty:\n"
        "    assert_type(empty, tuple[()])\n"
        "with names(42) as (number,):\n"
        "    assert_type(number, Named[int])\n"
        "with names(42, 'project') as (user, resource):\n"
        "    assert_type(user, Named[int])\n"
        "    assert_type(resource, Named[str])\n"
        "    write(resource, admin.prove(resource))\n"
        "with names(1, '2', 3.0, b'4', True, 6j, None, ['8']) as eight:\n"
        "    assert_type(eight, tuple[Named[int], Named[str], Named[float],\n"
        "        Named[bytes], Named[bool], Named[complex], Named[None],\n"
        "        Named[list[str]]])\n"
        "    assert_type(eight[7].value, list[str])\n"
        "with names(1, 2, 3, 4, 5, 6, 7, 8, 9) as nine:\n"
        "    assert_type(nine, tuple[Named[Any], ...])\n"
        "dynamic: list[object] = [1, 'project']\n"
        "with names(*dynamic) as unknown:\n"
        "    assert_type(unknown, tuple[Named[Any], ...])\n"
        "Names[Named[int]]\n"
    )
    command = [sys.executable, "-m", checker]
    if checker == "mypy":
        command += ["--strict"]
    else:
        command += [
            "check",
            "--preset",
            "default",
            "--python-interpreter-path",
            sys.executable,
        ]
    result = subprocess.run(
        [*command, str(valid)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    invalid = tmp_path / "invalid.py"
    invalid.write_text(
        valid.read_text()
        + "write(project, plan.prove(project))\nwrite(project)\n"
        + "with names(42, 'project') as (user, resource):\n"
        + "    user.value.upper()\n"
        + "    resource.value.not_a_real_method()\n"
        + "with names(42, 'project') as (only_one,):\n"
        + "    pass\n"
    )
    result = subprocess.run(
        [*command, str(invalid)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 1, result.stdout + result.stderr
    output = result.stdout + result.stderr
    if checker == "mypy":
        assert "[arg-type]" in output
        assert "[call-arg]" in output
    else:
        assert "[bad-argument-type]" in output
        assert "[missing-argument]" in output
    assert '"upper"' in output or "`upper`" in output
    assert "not_a_real_method" in output
    assert "unpack" in output.lower() or "values" in output.lower()
