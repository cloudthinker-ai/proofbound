# Core comparison

## Question

Is Proofbound's Rust core faster or more efficient than rauchg/gdp-ts?
Benchmark the shipped designs without changing either runtime implementation.

## Cases and checks

- Baseline checksum loop to expose harness/optimizer floor.
- Fresh naming at supported arities one, two and three.
- Proof creation at arities zero through three, with names created before timing.
- Typed Rust proof creation at arity two to expose wrapper allocations separately.
- Protected calls with preissued two-subject proofs: raw and typed Rust verification
  compared with the upstream pattern's statically checked proof argument.
- Complete fresh-name/proof/protected-call flow for two subjects.
- Runtime-scoped flow with explicit close on Rust; TS scope is compile-time-only.
- Every measured batch must match a deterministic independent checksum oracle.
- Rust's runtime checks reject wrong issuer, swapped subjects and closed scopes
  before each process measures work. These guards are outside timed batches.

## Method

Use a dedicated Ubuntu 24.04 GitHub Actions VM because the shared development
host currently has load far above its 32 CPUs. Pin both subprocesses to one CPU.
Use release Rust 1.90.0 and Node 22.23.2's actual TypeScript source execution,
pinned to upstream revision ebd0af9cae423997a43a024dc6d6738b0895bbec.
No npm dependencies, TypeScript rewrites, copied/faster proxy implementation,
Python wrapper, application I/O or policy queries enter the measurements.

Two repetitions, nine alternating-order subprocess samples each, two warmup
batches per subprocess, one million operations per batch. Report median and
nearest-rank p95 for internal wall and CPU time, and whole-process peak RSS.
Rust is single-threaded and reads scheduler runtime in nanoseconds; Node's CPU
usage includes all process threads. External GNU time records total process
wall/user/system CPU and peak RSS, including startup and warmups.

Rust black-boxes inputs, handles, proofs and results. JS consumes dynamic inputs
and checksums, retains the last returned proof and verifies the real upstream
cached/frozen-token invariant. JIT elision of phantom proof work is legitimate;
results close to the checksum loop floor are labelled accordingly.

The benchmark is measurement tooling over existing APIs; it adds no product
architecture or authorization behavior and needs no architectural plan review.
The Rust example, JS harness, Python orchestrator and manual private workflow
are the only code additions. Runtime code and dependencies stay unchanged.

## Interpretation

Do not label checksum equality as equal guarantees. The TS implementation mostly
erases proof relationships after type checking and reuses one token. Rust stores
identities, checks issuer/subjects and supports runtime scope expiry, with real
allocation and atomic-reference costs. Cross-runtime RSS includes the Node VM
and is not per-proof memory. Report the measured winner per operation and avoid
a blanket language-speed or security ranking.

The upstream bench directory measures type-checker cost, which is a separate
question; this comparison measures runtime library overhead only.
