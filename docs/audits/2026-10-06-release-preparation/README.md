# Python release preparation

This records preparation before publication. The subsequent public release and
fresh PyPI installation are documented in the
[publication record](../2026-10-06-publication/README.md).

Candidate `2c9f2c25dcdecfd4e15eb65f3c81da16a9509247` prepares `gdp-rs==0.1.0` as an experimental
release. The `gdp` import, Rust crate name and runtime code remain unchanged.
The package includes alpha status, project links, an installation guide,
guarantee limits and upstream attribution. The original MIT license is preserved.

[Private draft release v0.1.0](https://github.com/cloudthinker-ai/proofbound/releases)
contains the four tested platform wheels, source archive and SHA256SUMS.
The draft is not a public release; PyPI upload and repository visibility remain
separate approval steps under AGENTS.md.

## Checks

- `make check`, `make wheel`, `make package-check`, workflow lint and recognized PyPI classifiers pass.
- The fresh local wheel and the staged portable Linux wheel each pass all 46 Python tests, the SQLite example and lint; consumer tests include mypy and Pyrefly.
- All nine jobs passed in [candidate CI](https://github.com/cloudthinker-ai/proofbound/actions/runs/37437554808): four platform-wheel jobs, four Python contract jobs and the dependency advisory audit.
- Every staged wheel passes name/version, alpha status, project-URL, typing-file and byte-identical license validation. The source archive metadata and licenses also match.
- A Windows-style checkout regression confirms `.gitattributes` preserves all three original LICENSE files byte for byte.
- The Infisical-provided token is present and has PyPI format; its value never enters files or logs.
- `uv publish --dry-run` targeting `https://upload.pypi.org/legacy/` checks exactly five files and exits successfully. It uploads nothing and does not prove token permission to create the project.

- Gitleaks 8.30.1 scanned all 13 candidate commits and found no secrets. GitHub asset digests match the staged manifest for all five package files.

## Reviewed files

All files come from the same candidate CI run. The Linux wheels target glibc
2.17. SHA256SUMS is attached to the
private draft and omitted from the PyPI upload glob.

| Filename | Bytes | SHA-256 |
| --- | ---: | --- |
| gdp_rs-0.1.0-cp311-abi3-macosx_11_0_arm64.whl | 234066 | `84826359bfb2ea4573bd207f5a33d32673fb8d879712981d44f7d2defde49ce8` |
| gdp_rs-0.1.0-cp311-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl | 259680 | `0136118d23a399067fdf98f12d5a1d321c140c7635b666a2a913ed0b6073a689` |
| gdp_rs-0.1.0-cp311-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl | 259822 | `d0855d1c0424c64d9c9db2e67bf20ac9b50b39b10b46f950c7f9f27bf798a3a5` |
| gdp_rs-0.1.0-cp311-abi3-win_amd64.whl | 139723 | `249a7f3f8e3649b5ae57d6ab9103b6aad82a9b80c5b9683a5c50e13ba0574e6e` |
| gdp_rs-0.1.0.tar.gz | 25551 | `6ccf3e770f0f81c12155409b9723b9b5355e1d62b81820c7eff05ab3108ee47d` |

[Machine-readable manifest](manifest.json) preserves the source commit and run.
No package has been uploaded to PyPI during preparation. The token is only read
by the Infisical child process. No registry release or visibility change occurred.
