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

## Verified result

The private [benchmark run](https://github.com/cloudthinker-ai/proofbound/actions/runs/37421618083)
completed on 2026-10-06 using an Ubuntu 24.04 Azure VM with an AMD EPYC 7763
and two logical CPUs. Both implementations were pinned to CPU 0. Recorded load
values were 0.66, 1.40 and 1.79, below the available CPU count. All 468 samples passed output
checks; each Rust process also passed the runtime rejection checks.

The table gives wall-time median ranges across the two repetitions, including
the checksum loop. Each median represents nine batches of one million operations.
Full wall/CPU median and p95 tables and raw samples are in the
[evidence report](audits/2026-10-06-core-comparison/README.md).

| Operation | Rust median, ns/op | gdp-ts median, ns/op |
| --- | ---: | ---: |
| Baseline checksum loop | 0.90–0.92 | 1.85–1.88 |
| One fresh name | 20.33–20.51 | 82.63–82.65 |
| Two fresh names | 41.14–41.38 | 129.22–129.23 |
| Three fresh names | 62.28–62.68 | 174.92–174.96 |
| Raw proof, no subjects | 20.56–20.64 | 4.72–4.92 |
| Raw proof, one subject | 29.28–29.60 | 4.85–4.92 |
| Raw proof, two subjects | 39.76–40.03 | 4.76–4.90 |
| Raw proof, three subjects | 51.44–51.59 | 4.62–4.87 |
| Typed proof, two subjects | 102.01–104.34 | 4.59–4.66 |
| Raw verification / upstream proof-accepting call | 5.50–6.12 | 1.84–1.85 |
| Typed verification / upstream proof-accepting call | 52.37–53.72 | 1.83–1.84 |
| Complete typed two-subject flow | 177.82–177.85 | 130.23–130.43 |
| Raw runtime scope flow / upstream compile-time scope flow | 81.45–82.45 | 130.23–130.85 |

The result is mixed. Rust naming is 2.79–4.07× faster across these arities. The
raw runtime scope flow is 1.59–1.60× faster despite performing runtime checks
and explicit scope close. This raw case uses core identity handles directly;
it excludes a language adapter's payload handling or boundary cost. The typed
Rust flow is about 1.36× slower than upstream. Upstream's cached token is much
cheaper to return than allocating Rust proofs, and its proof-accepting call is
near the baseline floor because it performs no runtime identity verification.

Rust's typed wrapper currently constructs temporary handle vectors for proof
creation and verification. The separate raw/typed cases expose additional
wrapper overhead; this is a candidate for future profiling and optimization.
These measurements do not support a blanket claim that our core is faster.

Whole-process peak RSS medians are 1.86–2.07 MiB for Rust versus 68.54–71.78 MiB
for Node. This includes Node's VM and does not measure per-proof memory or the
Python binding. Scheduler CPU accounting visibly rounds short Rust batches;
internal wall time is the primary comparison here. P95 values are batch-time
quantiles, not individual-operation latency percentiles.
