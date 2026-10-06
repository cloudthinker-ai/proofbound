# Rust and gdp-ts runtime comparison

This benchmark compares Proofbound's existing Rust core with Guillermo Rauch's
unchanged [gdp-ts](https://github.com/rauchg/gdp-ts) at revision
`ebd0af9cae423997a43a024dc6d6738b0895bbec`. It measures library overhead, excluding
Python, application I/O, policy queries and TypeScript compilation.

The implementations enforce different runtime contracts. Upstream creates one
frozen proof token per issuer and reuses it; subject relationships are checked
by TypeScript. Proofbound allocates proofs holding subject identities and checks
exact issuer, ordered subjects and live scopes at runtime. Matching checksums
establish matching outputs, not equivalent authorization guarantees.

## Reproduce

Use Linux with GNU time, Rust 1.90.0 and the Node version in `.nvmrc`. Clone the
upstream repository separately and check out the pinned revision:

```bash
git clone https://github.com/rauchg/gdp-ts.git /tmp/gdp-ts-benchmark
git -C /tmp/gdp-ts-benchmark checkout ebd0af9cae423997a43a024dc6d6738b0895bbec
cargo build --release --locked -p gdp --example bench_core
python3 scripts/bench_core.py --upstream /tmp/gdp-ts-benchmark --output .bench/results
```

The private manual [Core comparison workflow](../.github/workflows/core-benchmark.yml)
does the same on an Ubuntu 24.04 runner and uploads raw results. It does not change
repository visibility or publish packages.

The harness pins all processes to one CPU. Each of two repetitions uses nine
alternating-order samples per implementation and case. Every process runs two
warmup batches and one measured batch of one million operations. Each result
must match an independent arithmetic checksum. Before timing, Rust also checks
wrong-issuer, swapped-subject and expired-scope rejection. Node imports the real
upstream TypeScript source without rewriting it or installing dependencies.

## Read the measurements

Internal wall time excludes startup and warmups. CPU time uses Linux scheduler
runtime for the single-threaded Rust executable and process CPU usage for Node,
including its runtime threads. GNU time records whole-process startup, warmups
and measured work separately. Peak RSS includes the Node VM and is not a measure
of memory per proof. Raw JSON preserves samples, median, nearest-rank p95,
versions, revisions, CPU model, affinity and host load.

`name1` through `name3` create fresh names. `prove0` through `prove3` issue proofs
over names created before timing. `typed_prove2` adds Rust's typed wrapper.
`runtime_require2` and `typed_require2` compare actual Rust verification with
the upstream protected-function pattern accepting a statically checked proof;
upstream performs no corresponding runtime subject verification. `typed_flow2`
creates two names, issues a proof and calls the protected operation.
`runtime_scope_flow2` additionally creates and closes a Rust runtime scope;
upstream has only compile-time scoping. These labels do not imply equal work.

Rust black-boxes handles and values. JavaScript consumes dynamic inputs and
checksums, retains its last proof and checks upstream's frozen-token reuse.
JIT elimination of erased proof work is part of the shipped design. Results
near the baseline loop floor should not be interpreted as precise standalone
proof-operation costs. The upstream `bench/` measures type-checker cost, which
is a separate question.
