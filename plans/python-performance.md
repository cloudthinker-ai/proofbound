# Python performance

## Problem

The Python decorator binds and applies signature defaults on every protected
call. Lint scans build a parent map for every AST even when no issuer is defined,
and directory scans enumerate excluded dependencies before skipping them.

## Scope

Optimize existing decorator and lint paths. Keep the Rust core, public API,
diagnostic codes/order, proof semantics, and application policy unchanged.
No CloudThinker backend integration or backend speed claim is included.
This preserves existing call stacks; the architectural plan-review gate does
not apply. No new dependencies, registry publication, or visibility change.

## Correctness

- Actual proofs, issuer identity, ordered subjects, and scope liveness are checked
  on every call, including warmed call layouts and after cache eviction.
- Positional-only, keyword-only, defaults, positional proof arguments, variadic
  calls and keyword order retain `Signature.bind` validation. Invalid layouts
  retain the original TypeError messages before side effects.
- A layout cache holds at most 128 entries per function and retains no supplied
  argument, proof, subject, evidence, or authorization result. Declared function
  defaults retain their original lifetime.
- Async checks execute when awaited; signatures remain visible to FastAPI.
- Lint preserves complete, sorted diagnostics, explicit paths under excluded
  ancestors, hidden application folders, and unreadable matching directories.
- Existing SQLite/HTTP/GC/type/lint tests run alongside added real SQLite
  call-layout, request-retention and CLI traversal regressions.

## Implementation

| File | Change |
| --- | --- |
| `bindings/python/python/gdp/contracts.py` | Compile a verifier at decoration time; validate each new `(positional count, ordered keyword names)` with `Signature.bind`; cache readers rather than bound values |
| `bindings/python/python/gdp/lint.py` | Build AST parents with a cached property only when a definition needs them; discover files with pruned `os.walk` and retain sorted output |
| `bindings/python/tests/proofs/test_contracts.py` | Real SQLite checks across calling patterns, invalid layouts, cache churn, expiry and collectible request values |
| `bindings/python/tests/test_lint.py` | CLI discovery/order/errors for excluded and explicit inputs |
| `scripts/bench_python.py` | Same-process paired baseline/current benchmark with two warmups, nine alternating samples, output parity, CPU/wall medians and p95, and raw JSON |
| `Makefile` | `bench` builds release before measurement |
| `AGENTS.md`, `README.md`, `wiki/proof-contracts.md`, `docs/performance.md` | Record cache invariants, benchmark commands and verified limits |

## Measurement

Baseline: private repository revision `95aaa9f`, compiled with release settings
and snapshotted as a separate installed package. Candidate and baseline run
in one interpreter on the same synthetic cases. Include direct native calls
at arities 0, 1, 2, 8 and 64 as unchanged controls, scoped issue/verify, rejection,
sync/default/variadic/multiple-proof/async calls, a 500-line lint source, and a
tree containing 16 application files plus 1,000 excluded dependency files.

Initial profile confirmed repeated signature binding as a major Python cost.
Initial paired run showed 1.76–3.35x CPU improvements for protected calls and
1.33x for a large-file lint check. A further change replaced separate subject
collection and type-check generator passes with one checked loop.
Use a fixed CPU affinity for A/A and repeated A/B measurements; record shared-host
load and keep wall/CPU figures separate. This host is oversubscribed, so do not
translate microbench results into production endpoint latency or throughput.

## Completion

Keep only repeatable paired improvements with unchanged outputs and passing
`make check`, rebuilt distributions, and a fresh installed-wheel test.
Document raw measurements and variability. Do not add a noisy timing threshold
to CI; correctness runs across the existing Python/platform matrix.

## Results

Two final release comparisons confirmed 3.23–5.06x synchronous protected-call
CPU improvements, 2.39–2.50x async-batch improvements, 1.35–1.50x source lint,
and 35.02–35.15x scans of a tree containing 1,000 excluded files. Medians and p95
improved for CPU and wall time in both runs. Unchanged binary/scoped controls
remained within approximately 10% measurement variability.

All 8,616 backend application files retained identical ordered diagnostics.
Local checks, distribution rebuilds and all 46 installed-wheel tests passed.
The results and raw samples are in `docs/performance.md` and
`docs/audits/2026-10-06-python-performance/`. The backend checkout is untouched.
