# Security patch verification

Review baseline: main `5b8645826090b46004cc1a7d9a6244c17e764a73` and the
installed public `gdp-rs==0.1.0` wheel. Owner authorized all fixes, GitHub
hardening, commit/push and publication of 0.1.1.

Both new regressions failed against the public 0.1.0 wheel:

```bash
.bench/pypi-verify/bin/python -m pytest \
  bindings/python/tests/proofs/test_contracts.py::test_callable_instances_are_rejected_before_deferred_side_effects \
  bindings/python/tests/test_lint.py::test_unreadable_directories_fail_the_lint_command -q
```

Result: two failures. Callable instance decoration did not raise, and directory
lint returned 0 instead of 1. The original reproduction showed SQLite side
effects after scope expiry for async/generator callable instances; ordinary
async functions and direct core verification rejected the expired proof.

The fixed implementation rejects unsupported callable instances before use,
retains normal function/method/partial support, and reports directory traversal
failures as GDP000. The new regressions use real SQLite operations and OS
permissions. Permission cases run unprivileged on POSIX; Windows/root skip only
that permission-dependent case. Existing tests cover opaque handles, all proof
rejection shapes, active scopes, FastAPI, type checking and installed packages.

Further partial checks reproduced hidden async execution in a partial subclass
and wrong-subject execution after rebinding a partial keyword. The same SQLite
regression now rejects subclasses and checks that original keyword mutation
cannot change protected default bindings.

Cross-platform CI caught a regression-test assumption on Python 3.13: its
built-in partial constructor flattens a partial subclass into the underlying
function before GDP sees it, while older versions retain the subclass as a
call target. The test now checks the actual subclass directly on every version,
alongside ordinary callable-instance partials. No runtime guard was relaxed.

Before the patch, cargo-audit found no advisories among 16 Rust dependencies;
OSV found no matching advisories among 27 installed Python distributions;
Gitleaks found no secrets in all 16 commits. Repository settings were verified
through GitHub's authenticated API. Private reporting and Dependabot alerts
were already enabled; scanning, push protection and automatic security updates
were enabled for this patch.

## Published verification

Candidate `289170fe6914118702a9c9671a7ae3e9bb981bf0` passed all nine jobs in
[CI run 37443068104](https://github.com/cloudthinker-ai/proofbound/actions/runs/37443068104).
The four platform wheels passed their installed tests on CPython 3.11–3.14.
POSIX platforms passed 48 tests; Windows passed 47 with the permission-dependent
directory case skipped. Local make check, release packaging, installed wheels,
type checkers, examples, cargo-audit and full-redaction secret scans passed.

Published [gdp-rs 0.1.1](https://pypi.org/project/gdp-rs/0.1.1/) and
[GitHub v0.1.1](https://github.com/cloudthinker-ai/proofbound/releases/tag/v0.1.1).
The tag points to the exact candidate. All five public PyPI files matched the
SHA-256 values in [manifest.json](manifest.json). Original MIT license bytes
remain identical in every artifact. The upload token entered only Infisical's
child process and was neither persisted nor displayed.

A fresh public PyPI install on CPython 3.14.7 used --no-cache and
--only-binary=:all:. The installed package version and environment location
were verified. All 48 tests passed with deprecation warnings as errors;
SQLite authorized/wrong-project examples and the installed lint command passed.
Publication receipts are [pypi-receipt.json](pypi-receipt.json) and
[github-receipt.json](github-receipt.json).

Final GitHub controls include secret scanning, push protection, automatic
Dependabot security updates and weekly Cargo/Python/Actions update PRs. Main's
protection requires one approval, stale-review dismissal, all nine CI contexts
from GitHub Actions, up-to-date branches and resolved conversations; it applies
to administrators and rejects force pushes and branch deletion. Push CI targets
main; every PR still runs all checks, avoiding duplicate bot branch builds.
The API verification receipt is attached to the public release as
[security-controls.json](https://github.com/cloudthinker-ai/proofbound/releases/download/v0.1.1/security-controls.json).

The two original findings and the related partial rebinding/subclass cases are
fixed. Correct policy, revocation, mutable payloads, atomic check/write and
hostile in-process reflection remain the documented application boundary.
