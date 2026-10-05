# Verification

The initial port was verified locally on 2026-10-05 with Rust 1.90.0 and CPython
3.12. The independent repository is private at https://github.com/cloudthinker-ai/gdp.

| Check | Evidence |
| --- | --- |
| Rust public API | Four contract tests plus six invalid programs compiled by one negative-test harness |
| Rust/Python fault boundary | Binding fault test contains a panic and discards its payload |
| Python sensitive API | 33 tests: real SQLite writes, sync/async, wrong subjects/kinds/issuers, expiry, opaque classes, lint, typing, ABI and stub contract |
| Static quality | Cargo format and Clippy with warnings denied; Ruff lint/format; mypy |
| Dependencies | cargo-audit 0.22.2: no vulnerabilities or warnings; core has no dependencies |
| Distribution | Wheel rebuilt from the source distribution; Rust crate package verifies; license and typing contract checked in archives |
| Fresh installations | Clean Python 3.11 and 3.14 wheel installations exercised the initial 30-test suite and SQLite example |
| Private source install | uv installed directly from the GitHub repository; the protected SQLite example and gdp-lint ran successfully |
| Adoption guidance | Separate Python consumer and Rust consumer followed the skill; real operations and negative contracts passed |

The CI workflow repeats the current full suite, builds from the source distribution,
and tests a fresh wheel installation on Python 3.11, 3.12, 3.13, and 3.14. See
[GitHub Actions](https://github.com/cloudthinker-ai/gdp/actions) for the commit-specific
results and private wheel artifacts.

This verifies the library boundary, not an application migration. The port introduces
no CloudThinker endpoint, policy decision, or product-agent behavior. Additional
language adapters are documented extension points; Rust and Python are implemented.
