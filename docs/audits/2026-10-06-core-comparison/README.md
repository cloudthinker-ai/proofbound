# Core runtime comparison evidence

Measured 2026-10-06 at 13:03–13:05 UTC+7 in private
[Actions run 37421618083](https://github.com/cloudthinker-ai/proofbound/actions/runs/37421618083).
[Interpretation and reproduction](../../core-performance.md) define each case.

- Proofbound: `3d9a4478c71612443c296b2224d6288adc6e5581`; runtime source unchanged by the benchmark commit.
- Upstream: `ebd0af9cae423997a43a024dc6d6738b0895bbec`; imported directly from the unmodified checkout.
- Rust: `rustc 1.90.0 (1159e78c4 2025-09-14)`; release profile, optimization 3, LTO, one codegen unit.
- Node: `v22.23.2`; native TypeScript loading, no npm dependencies.
- Host: Ubuntu 24.04 Azure VM, AMD EPYC 7763, two logical CPUs, affinity CPU 0.
- Initial load: 0.66, 0.23, 0.08; recorded loads were below two CPUs.
- Samples: two repetitions × nine samples × one million measured operations per implementation/case; two additional warmup batches per process.
- Checks: all 468 samples match the independent checksum oracle; every Rust process also passes runtime rejection guards.
- JSON SHA-256: `e362c83888ef2b597422985a659e4f15fe9a9c0be644d7973d33a324d4078be4`.

Times include the checksum loop and use ns per operation. The baseline exposes
that loop's floor. The p95 is nearest rank over nine batch samples, so it equals
the largest sample; it is not the latency distribution of individual calls.
Linux scheduler CPU accounting is updated periodically and produces visible
rounding in short Rust batches. Prefer internal wall time for comparisons at
these small durations; the two CPU clocks also count different thread sets.

## Repetition 1

| Case | Rust wall median / p95, ns | gdp-ts wall median / p95, ns | Rust CPU median / p95, ns | gdp-ts CPU median / p95, ns |
| --- | ---: | ---: | ---: | ---: |
| baseline | 0.92 / 1.02 | 1.88 / 3.31 | 1.00 / 1.01 | 1.92 / 1.92 |
| name1 | 20.33 / 21.36 | 82.65 / 84.09 | 20.00 / 20.99 | 82.69 / 84.15 |
| name2 | 41.38 / 42.71 | 129.23 / 134.22 | 41.96 / 42.96 | 129.25 / 134.24 |
| name3 | 62.68 / 67.18 | 174.92 / 182.07 | 63.00 / 67.00 | 174.94 / 182.06 |
| prove0 | 20.64 / 21.49 | 4.92 / 5.36 | 21.00 / 22.00 | 4.96 / 5.16 |
| prove1 | 29.60 / 32.50 | 4.85 / 5.30 | 29.99 / 31.98 | 4.88 / 5.13 |
| prove2 | 39.76 / 41.19 | 4.76 / 4.97 | 40.00 / 42.00 | 4.79 / 5.01 |
| prove3 | 51.44 / 52.49 | 4.62 / 5.04 | 51.98 / 53.00 | 4.65 / 5.05 |
| typed_prove2 | 104.34 / 106.91 | 4.59 / 5.01 | 103.99 / 107.00 | 4.63 / 5.05 |
| runtime_require2 | 5.50 / 10.94 | 1.84 / 1.88 | 6.00 / 10.99 | 1.86 / 1.91 |
| typed_require2 | 52.37 / 53.92 | 1.84 / 1.88 | 53.00 / 54.00 | 1.86 / 1.91 |
| typed_flow2 | 177.82 / 208.70 | 130.23 / 134.09 | 177.96 / 206.87 | 130.26 / 134.13 |
| runtime_scope_flow2 | 82.45 / 84.61 | 130.85 / 136.14 | 82.99 / 83.99 | 130.89 / 136.18 |

Runner load after repetition: 1.40, 0.51, 0.19 (1 / 5 / 15 minutes; two available logical CPUs).

## Repetition 2

| Case | Rust wall median / p95, ns | gdp-ts wall median / p95, ns | Rust CPU median / p95, ns | gdp-ts CPU median / p95, ns |
| --- | ---: | ---: | ---: | ---: |
| baseline | 0.90 / 0.93 | 1.85 / 1.88 | 1.00 / 1.13 | 1.88 / 1.91 |
| name1 | 20.51 / 20.82 | 82.63 / 86.49 | 20.00 / 21.00 | 82.67 / 86.53 |
| name2 | 41.14 / 42.17 | 129.22 / 140.03 | 41.99 / 42.00 | 129.25 / 140.07 |
| name3 | 62.28 / 64.13 | 174.96 / 186.03 | 62.00 / 64.00 | 174.97 / 186.06 |
| prove0 | 20.56 / 20.69 | 4.72 / 5.02 | 20.98 / 21.00 | 4.76 / 5.06 |
| prove1 | 29.28 / 32.39 | 4.92 / 5.06 | 29.00 / 33.00 | 4.96 / 5.06 |
| prove2 | 40.03 / 58.67 | 4.90 / 5.04 | 40.00 / 59.00 | 4.92 / 5.05 |
| prove3 | 51.59 / 52.46 | 4.87 / 5.01 | 52.00 / 52.00 | 4.90 / 5.04 |
| typed_prove2 | 102.01 / 106.25 | 4.66 / 5.75 | 102.00 / 106.99 | 4.70 / 5.14 |
| runtime_require2 | 6.12 / 8.70 | 1.85 / 1.88 | 5.99 / 9.00 | 1.87 / 1.92 |
| typed_require2 | 53.72 / 70.22 | 1.83 / 1.89 | 53.99 / 69.98 | 1.85 / 1.92 |
| typed_flow2 | 177.85 / 191.02 | 130.43 / 135.01 | 177.98 / 190.98 | 130.43 / 135.06 |
| runtime_scope_flow2 | 81.45 / 83.69 | 130.23 / 134.35 | 82.00 / 84.00 | 130.22 / 134.35 |

Runner load after repetition: 1.79, 0.76, 0.29 (1 / 5 / 15 minutes; two available logical CPUs).

## Memory

Across case/repetition medians, whole-process peak RSS is
1.86–2.07 MiB for the Rust executable and 68.54–71.78 MiB for Node.
These figures include startup and all warmups. They describe the cost of each
process, including Node's VM, and cannot establish memory efficiency per proof
or Python application memory usage. Individual RSS samples remain in the JSON.

## Verification

`make check`, `make wheel`, `make package-check`, workflow lint and JavaScript
syntax checks passed. A fresh wheel installation on CPython 3.14.7 passed all
46 Python tests and the SQLite example. The dedicated benchmark completed
successfully; no runtime implementation or dependency changed.
