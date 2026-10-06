import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from check_artifacts import check_wheel


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify and test a fresh wheel install"
    )
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--platform", required=True)
    args = parser.parse_args()
    wheels = list(args.dist.glob("*.whl"))
    if len(wheels) != 1:
        raise ValueError("Expected exactly one platform wheel")
    wheel = wheels[0].resolve()
    if not wheel.name.endswith(f"-{args.platform}.whl"):
        raise ValueError("Wheel does not match the expected platform")
    if "-cp311-abi3-" not in wheel.name:
        raise ValueError("Wheel must support the CPython 3.11 stable ABI")
    check_wheel(wheel, Path("LICENSE").read_bytes())
    with zipfile.ZipFile(wheel) as archive:
        metadata = next(
            name for name in archive.namelist() if name.endswith("/METADATA")
        )
        if "Requires-Python: >=3.11" not in archive.read(metadata).decode():
            raise ValueError("Wheel is missing the supported Python version contract")
    with tempfile.TemporaryDirectory(prefix="proofbound-wheel-") as folder:
        environment = Path(folder) / "venv"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(environment)], check=True
        )
        python = environment / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--only-binary=:all:",
                str(wheel),
                "-r",
                "requirements-dev.txt",
            ],
            check=True,
        )
        subprocess.run(
            [
                str(python),
                "-c",
                "import gdp, sys; from pathlib import Path; "
                "assert Path(gdp.__file__).is_relative_to(Path(sys.prefix))",
            ],
            check=True,
        )
        for command in (
            [
                "-m",
                "pytest",
                "bindings/python/tests",
                "-q",
                "-W",
                "error::DeprecationWarning",
            ],
            ["examples/python/main.py"],
            ["-m", "gdp.lint", "examples/python"],
        ):
            subprocess.run([str(python), *command], check=True)
    print(f"Verified and tested {wheel.name}")


if __name__ == "__main__":
    main()
