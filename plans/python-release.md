# Python release preparation

Prepare `gdp-rs==0.1.0` for a separately approved PyPI upload using
`UV_PUBLISH_TOKEN` injected by Infisical. Retain the `gdp` import and Rust crate
names, preserve upstream attribution and leave runtime behavior unchanged.

The design gate is skipped: metadata and documentation extend the existing
build/check flow without a new application architecture or agent flow.

## Cases

- Release artifacts contain their own installation guidance, guarantee limits,
  alpha status, project URLs and upstream attribution.
- Cargo and Python versions match; wrong metadata fails the existing artifact
  checker before upload.
- All four platform wheels come from the exact green candidate CI run. The
  source archive comes from the same run. Local platform wheels stay out of the
  upload directory.
- Infisical provides the token without writing or printing its value. An explicit
  PyPI dry run performs no public upload and does not assert token authorization.
- Publication exposes source even while GitHub is private. Public GitHub
  visibility and registry upload remain separate owner decisions under AGENTS.md.
- Current-tree internal machine paths are sanitized. History remains unchanged;
  no cleanup claims historical removal.

## Changes and verification

Update Python project metadata and its packaged README, main installation docs,
security reporting, first release notes, publication guidance and wiki index.
Extend `scripts/check_artifacts.py` to validate built wheel metadata and version
agreement. Run formatting/lint, `make check`, package rebuilds, installed-wheel
tests, CI, metadata checks over all downloaded platform wheels, history secret
scan, archive checksum recording and an Infisical-backed upload dry run.

No public upload, visibility change, crates.io publication or credential
persistence is part of preparation. Ask for the final publication decision only
after the candidate and artifacts are concrete and reviewable.

## Cross-platform preparation check

Candidate `1e6b6ec` passed all four wheel jobs. Comparing those wheels together
found that Windows checkout changed the packaged license to CRLF: 1,093 bytes
versus the original 1,072, with identical text after newline normalization.
Set `eol=lf` for the three LICENSE paths through `.gitattributes`, then rebuild
the candidate and require byte-identical original licenses on every platform.
