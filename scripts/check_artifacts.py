import tarfile
import tomllib
import zipfile
from pathlib import Path


def check() -> None:
    root = Path(__file__).resolve().parents[1]
    version = tomllib.loads((root / "Cargo.toml").read_text())["workspace"]["package"][
        "version"
    ]
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
        with zipfile.ZipFile(path) as archive:
            licenses = [
                item for item in archive.namelist() if item.endswith("/LICENSE")
            ]
            if not licenses or any(archive.read(item) != expected for item in licenses):
                raise ValueError(f"Missing or incorrect license in {path.name}")
            if (
                "gdp/py.typed" not in archive.namelist()
                or "gdp/_gdp.pyi" not in archive.namelist()
            ):
                raise ValueError("Missing Python typing contract")
    print("Rust and Python packages retain the license and typing contract")


if __name__ == "__main__":
    check()
