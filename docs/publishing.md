# Publishing Proofbound

The Python distribution is `gdp-rs`; its version must match the Rust workspace.
The 0.1 series is experimental. A PyPI upload and GitHub repository visibility
are separate actions requiring owner approval under [AGENTS.md](../AGENTS.md).
Preparing artifacts and a dry run do not publish them.

## Prepare

Run `make check`, `make wheel`, `make package-check`, and test an installed wheel.
Commit the candidate and wait for all nine jobs in the Proof contracts workflow.
Use that exact successful run for the four platform-wheel artifacts and the
`gdp-python-3.11` source distribution. Do not upload the local Linux wheel when
the release contains the tested manylinux2014 wheel.

Collect exactly four wheels and one source archive in `.bench/release/0.1.0/`.
Record their SHA-256 hashes separately and check package name, version, URLs,
alpha status, license and typing files. The archive includes the Rust core;
uploading it makes that source public even if GitHub remains private.

Credentials remain in Infisical. `uv publish` reads `UV_PUBLISH_TOKEN` directly;
never copy the token into a command, file, GitHub secret or log. Preview the
explicit PyPI target with:

```bash
infisical run --silent -- uv publish --dry-run --trusted-publishing never \
  --publish-url https://upload.pypi.org/legacy/ \
  --check-url https://pypi.org/simple/ \
  .bench/release/0.1.0/*.whl .bench/release/0.1.0/*.tar.gz
```

A dry run checks preparation without uploading. It does not establish that the
token has permission to create the project. Recheck PyPI for an existing version
before the approved upload; published filenames cannot be reused.

## Publish after approval

For an approved public GitHub launch, change visibility, enable private
vulnerability reporting and publish `v0.1.0` with the release notes and tested
artifacts. Remove the pending-publication wording from the repository README.
Review history when deciding which internal planning or machine metadata should
be public: editing the current tree does not erase earlier commits.

For the approved PyPI upload, repeat the dry-run command without `--dry-run`.
Use only the previously reviewed files. Do not publish the Rust crate with a
PyPI token. Verify the PyPI JSON lists exactly the five expected files with
matching SHA-256 hashes, then install `gdp-rs==0.1.0` from PyPI into a fresh
environment without compiling and run the tests, example, lint and consumers.
