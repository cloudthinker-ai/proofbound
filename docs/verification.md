# Verification

Proofbound became public and `gdp-rs==0.1.0` was published to PyPI on 2026-10-06.
All five published package hashes match the tested release candidate manifest.
The release candidate passed all nine CI jobs in
[run 37437554808](https://github.com/cloudthinker-ai/proofbound/actions/runs/37437554808).
See the [release notes](releases/0.1.0.md) and
[publication evidence](audits/2026-10-06-publication/README.md).

Python performance improvements were verified on 2026-10-06. Code revision
`13664c4045689e1533ba669a41a88f569e6dbb8b` passed all nine CI jobs in
[run 37413254647](https://github.com/cloudthinker-ai/proofbound/actions/runs/37413254647).
All 46 Python tests pass across Python 3.11–3.14, including fresh platform wheels
on Linux x64/ARM64, macOS ARM64 and Windows x64. Distribution rebuilds, Rust
checks, static Python consumers, FastAPI/SQLite, lint and the advisory audit pass.

Two paired release comparisons confirm 3.23–5.06x synchronous protected-call CPU
improvements and 2.39–2.50x async-batch improvements. Source lint improves
1.35–1.50x; a scan with 1,000 excluded files improves about 35x. CPU and wall
medians/p95 improve in both runs. Every diagnostic sequence matches across
8,616 backend application files. See [measurement methods and raw evidence](performance.md).
These results cover Proofbound overhead; the backend has not adopted contracts
and its endpoint performance was not measured. These checks ran while the repository
and artifacts were private.

Python adoption improvements were verified on 2026-10-06. Code revision
`051d39b7af8a7f1118640445960e975a07455a47` passed all nine CI jobs
in [run 37409461865](https://github.com/cloudthinker-ai/proofbound/actions/runs/37409461865).
The repository and its wheel artifacts were private during that verification.

| Check | Evidence |
| --- | --- |
| Rust public API | Four contract tests plus six invalid programs compiled by one negative-test harness; core unchanged |
| Rust/Python fault boundary | Binding fault test contains a panic and discards its payload |
| Python sensitive API | 44 tests cover real SQLite writes, sync/async, wrong subjects/kinds/issuers, expiry, opaque classes, GC, HTTP, lint, typing, ABI and stub contract |
| GC regression | Four owning-handle cycles failed before the fix; unreachable cycles are now collected and reachable handles retain their documented behavior |
| Static typing | Mypy and Pyrefly preserve scoped types/tuple length through arity 8; reject missing/wrong proofs, invalid payload methods and unpacking; verify the 9/dynamic fallback |
| Lint regression | Explicit wrapper bypasses and relative private-issuer imports failed before the fix; GDP007 and relative GDP006 checks now reject them |
| HTTP boundary | FastAPI reads SQLite membership, writes only with valid proofs, returns value-free HTTP 403 for rejection, expires authority after response, and accepts a fresh subsequent request |
| Static quality | Cargo format and Clippy with warnings denied; Ruff lint/format; mypy and Pyrefly; actionlint 1.7.12 |
| Distribution | Wheel rebuilt from source distribution; Rust crate package verifies; identical licenses, API files, type stubs and metadata checked |
| Fresh installations | Linux x64/ARM64, macOS ARM64 and Windows x64 each test their native cp311-abi3 wheel on CPython 3.11, 3.12, 3.13 and 3.14; all 44 tests, lint and SQLite example run in independent environments |
| Installation without compilation | Wheel/development dependencies install with binary-only resolution; Linux x64 private artifact downloaded using gh and installed separately, then passed the SQLite example and lint |

The platform jobs upload wheels only after all four Python versions pass. Linux
wheels target glibc 2.17+, macOS ARM64 targets 11+, and Windows wheels target x64.
The advisory-audit job passed on the same implementation revision using
cargo-audit 0.22.2 with warnings denied; no vulnerabilities or warnings were reported.

The original port revision `c6ecae24d30b35be3bac6148fa6e52550edfef93` passed all five
jobs in [run 37342180432](https://github.com/cloudthinker-ai/proofbound/actions/runs/37342180432),
including cargo-audit 0.22.2 without vulnerabilities or warnings. Separate Python
and Rust consumers followed the adoption skill, and a private Git source install
was also verified at that original revision.

This verifies the library boundary, not an application migration. These changes
introduce no CloudThinker endpoint, policy decision, or product-agent behavior.
Additional language adapters remain extension points; Rust and Python are implemented.
