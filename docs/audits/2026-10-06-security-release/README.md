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

Release verification and final repository protection evidence are recorded
below after the exact candidate and public artifacts have been verified.
