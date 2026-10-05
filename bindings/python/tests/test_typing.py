import subprocess
import sys


def test_installed_types_reject_wrong_kinds_and_missing_proofs(tmp_path):
    valid = tmp_path / "valid.py"
    valid.write_text(
        "from gdp import Named, Proof, Requirement, define_proof, name, requires\n"
        "class Admin: pass\n"
        "class Plan: pass\n"
        "admin = define_proof('Admin', tag=Admin)\n"
        "plan = define_proof('Plan', tag=Plan)\n"
        "@requires(proof=Requirement(admin.kind, ('project',)))\n"
        "def write(project: Named[str], proof: Proof[Admin]) -> str:\n"
        "    return project.value\n"
        "project = name('project')\n"
        "write(project, admin.prove(project))\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", str(valid)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    invalid = tmp_path / "invalid.py"
    invalid.write_text(
        valid.read_text() + "write(project, plan.prove(project))\nwrite(project)\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", str(invalid)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "[arg-type]" in result.stdout
    assert "[call-arg]" in result.stdout
