# Proofbound 0.1.0 publication

Published on 2026-10-06:

- [gdp-rs 0.1.0 on PyPI](https://pypi.org/project/gdp-rs/0.1.0/).
- [Public Proofbound repository](https://github.com/cloudthinker-ai/proofbound).
- [GitHub release v0.1.0](https://github.com/cloudthinker-ai/proofbound/releases/tag/v0.1.0), marked experimental, with four platform wheels, the source archive and SHA256SUMS.

The release tag points to the tested candidate
`2c9f2c25dcdecfd4e15eb65f3c81da16a9509247`. That candidate passed all nine
[CI jobs](https://github.com/cloudthinker-ai/proofbound/actions/runs/37437554808).
The original MIT license and attribution remain intact.

All five PyPI SHA-256 values and the five matching GitHub asset digests equal
[the approved manifest](../2026-10-06-release-preparation/manifest.json).
Anonymous API reads verify that the repository, release and PyPI project are
publicly accessible. GitHub private vulnerability reporting is enabled.

## Fresh PyPI installation

A fresh CPython 3.12.3 environment installed `gdp-rs==0.1.0` directly from the
public PyPI index with cache disabled and binary-only resolution. The installed
package location was inside that environment and distribution version was 0.1.0.
No Rust compilation was used for installation.

The PyPI installation passed all 46 Python tests with deprecation warnings
raised as errors, including the installed mypy/Pyrefly consumers. The real SQLite
example accepted the authorized write and rejected the wrong-project proof.
The installed linter passed the example directory.

Credentials were injected into the upload process by Infisical without being
written to a file, command argument or log. Only the five reviewed package files
were uploaded; checksum files and local host wheels were excluded.

[PyPI receipt](pypi-receipt.json) records filenames, upload timestamps and hashes.
[GitHub receipt](github-receipt.json) records public release and asset digests.
