import tarfile
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path


def check_wheel(path: Path, expected: bytes) -> None:
    with zipfile.ZipFile(path) as archive:
        licenses = [item for item in archive.namelist() if item.endswith("/LICENSE")]
        if not licenses or any(archive.read(item) != expected for item in licenses):
            raise ValueError(f"Missing or incorrect license in {path.name}")
        required = {
            "gdp/py.typed",
            "gdp/_gdp.pyi",
            "gdp/__init__.py",
            "gdp/contracts.py",
        }
        if not required.issubset(archive.namelist()):
            raise ValueError("Missing Python typing or API contract")
        metadata_paths = [
            item for item in archive.namelist() if item.endswith("/METADATA")
        ]
        if len(metadata_paths) != 1:
            raise ValueError("Expected one wheel metadata document")
        metadata = Parser().parsestr(archive.read(metadata_paths[0]).decode())
        project = tomllib.loads(
            (
                Path(__file__).resolve().parents[1] / "bindings/python/pyproject.toml"
            ).read_text()
        )["project"]
        expected_headers = {
            "Name": project["name"],
            "Version": project["version"],
            "Requires-Python": project["requires-python"],
        }
        if any(metadata.get(key) != value for key, value in expected_headers.items()):
            raise ValueError("Wheel metadata does not match the release contract")
        if (
            metadata.get("Description-Content-Type", "").split(";", 1)[0].strip()
            != "text/markdown"
        ):
            raise ValueError("Wheel description must use Markdown")
        if not set(project["classifiers"]).issubset(metadata.get_all("Classifier", [])):
            raise ValueError("Wheel is missing supported classifiers")
        urls = dict(item.split(", ", 1) for item in metadata.get_all("Project-URL", []))
        if any(urls.get(key) != value for key, value in project["urls"].items()):
            raise ValueError("Wheel is missing release project URLs")


def check() -> None:
    root = Path(__file__).resolve().parents[1]
    version = tomllib.loads((root / "Cargo.toml").read_text())["workspace"]["package"][
        "version"
    ]
    if (
        tomllib.loads((root / "bindings/python/pyproject.toml").read_text())["project"][
            "version"
        ]
        != version
    ):
        raise ValueError("Rust and Python release versions differ")
    expected = (root / "LICENSE").read_bytes()
    archives = [
        root / f"target/package/gdp-{version}.crate",
        root / f"dist/gdp_rs-{version}.tar.gz",
    ]
    for path in archives:
        with tarfile.open(path) as archive:
            licenses = [item for item in archive if item.name.endswith("/LICENSE")]
            if not licenses:
                raise ValueError(f"Missing license in {path.name}")
            for item in licenses:
                stream = archive.extractfile(item)
                if stream is None or stream.read() != expected:
                    raise ValueError(f"Incorrect license in {path.name}")
    wheels = list((root / "dist").glob(f"gdp_rs-{version}-*.whl"))
    if not wheels:
        raise ValueError("Missing Python wheel")
    for path in wheels:
        check_wheel(path, expected)
    print("Rust and Python packages retain the license and typing contract")


if __name__ == "__main__":
    check()
