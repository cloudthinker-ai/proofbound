---
type: plan
description: Port gdp-ts to a reusable Rust core with Python support and publish it privately.
verified_at: 2026-10-05
status: DONE
commit: c6ecae24d30b35be3bac6148fa6e52550edfef93
---
# Port GDP

## Problem

Authorization checks disconnected from sensitive functions can be omitted. Port the
gdp-ts name/prove/require contract to Rust, support Python first, and upload the
independent library to a private cloudthinker-ai/gdp repository. Other languages
reuse the core through adapters; Python is the first completed adapter.

## Boundaries

- Build an independent library; do not migrate application endpoints in this task.
- Rust owns proof identity and verification, Python owns I/O and policy decisions.
- Python runtime checks compensate for the loss of Rust generative lifetimes at FFI.
- Preserve the upstream MIT license and explain the original research.
- If GitHub credentials cannot create a private repository, keep local work and report the blocker.

## Case Analysis

| Case | Outcome and recovery |
| --- | --- |
| CA-1 authorized user and entitled project | Both exact proofs admit the operation |
| CA-2 denied authorization | Trusted checker returns no proof, operation fails before side effects |
| CA-3 missing, wrong, or fake proof | Compile error in typed Rust; fixed authorization error in Python |
| CA-4 same raw ID named twice, swapped arguments, different issuer with same label | Identity mismatch rejects operation |
| CA-5 scope escape | Rust compilation rejects it; Python request usage is documented, optional scoped names expire at exit |
| CA-6 synchronous and asynchronous handlers | Decorator verifies before execution; async checker awaits I/O outside Rust |
| CA-7 mutable value and revocation | Document that proofs describe check-time facts; transactions remain consumer responsibility |
| CA-8 accidental issuer construction outside trusted modules | Python linter reports location without exposing values |
| CA-9 wrong wheel/stub ABI or direct constructor | Import fails closed; opaque classes reject Python construction and subclassing |
| CA-10 installed artifacts and private upload | Rust consumer and installed wheel work; GitHub confirms private visibility and exact pushed commit |

## Repo conventions to follow

- Existing backend Rust workspace shows PyO3 0.29 and abi3 CPython 3.11; use a separate
  binding crate so Rust users need no Python dependency or linker.
- Reuse the existing Rust 1.90 toolchain, lint baseline, and panic containment pattern.
- The user authorized a Rust port and private upload, so implement and verify without
  an additional plan approval. This standalone library is outside the service workspace.
- No Python fallback exists; absence or incompatible binding must fail at import.

## Rust seam and dependencies

Mode: port of the TypeScript contract, with a new Python in-process PyO3 library
seam. No Python implementation is being ported. The plain core does no I/O, logging,
or Python calls. No speed claim or service process is introduced.

| Source or dependency | Decision |
| --- | --- |
| gdp-ts TypeScript core | Rewrite its naming and proof contract; preserve license and attribution |
| Rust core | Standard library only; no runtime dependencies |
| PyO3 0.29 | Existing project binding technology; abi3 Python 3.11; advisory audit before upload |
| Compile-fail harness | Standard-library rustc subprocess; no trybuild dependency |
| Python AST linter | Python standard library; no parser dependency in the core |

Dependency check: PyO3 0.29.3 (MIT/Apache-2.0), released 2026-09-30, checked
with rust-kit crate_check.py: no affecting OSV advisory or CWE reported. Its unsafe
code wraps the CPython FFI and interpreter/reference ownership (1,334 textual unsafe
occurrences in src/); our own crates forbid unsafe. The lock contains 14 third-party
packages. cargo-audit 0.22.2 reports no vulnerabilities or warnings. No dependency
row blocks the port.

Both crates inherit unsafe_code=forbid and the existing denied Clippy baseline.
Libraries forbid printing; release uses optimization and unwind panic handling.
All Python objects are frozen, opaque, and non-subclassable. The extension exports
an exact integer interface version; one Python import location checks it. Faults
are contained inside src/py and errors never include subject values. Stubs and
py.typed ship with the wheel and have an export/member parity test.

Issuer creation is public as in upstream, but trusted modules keep issuers private.
Every consumer validates against a verifier bound to that specific issuer; a new
issuer with the same label or Rust marker cannot mint accepted proofs. Python lint
checks accidental issuer construction/export and proof minting outside proofs/.
This is an API integrity boundary, not an in-process sandbox against hostile code.

The reusable adapter boundary is the implemented gdp::runtime opaque handle API:
each adapter links the same Rust crate, owns language values, and passes handles.
Rust and Python ship now. Other languages can add bindings; no C ABI or remote
authority protocol is claimed. Never serialize handles into user-controlled IDs.

## Program Design

| Path | Change |
| --- | --- |
| Cargo.toml, Cargo.lock, rust-toolchain.toml, clippy.toml | new workspace/build contract |
| crates/gdp/src/{lib,typed,runtime}.rs | new language-independent core |
| crates/gdp/tests/ | new public Rust contract and compile rejection fixtures |
| bindings/python/src/py/ | new opaque extension classes and fixed exceptions |
| bindings/python/python/gdp/ | new API, sensitive-boundary decorator, AST linter, typing |
| bindings/python/tests/ | new real extension integration and type/lint contract checks |
| examples/ | new Rust and Python authorization/entitlement demonstration |
| docs/, wiki/, .agents/skills/gdp/ | new guarantees, adapter contract, adoption guidance |
| Makefile, .github/workflows/ci.yml, .gitignore | new repeatable checks and packaging |

Rust API:

```rust
pub fn name<T, R>(value: T, f: impl for<'id> FnOnce(Named<'id, T>) -> R) -> R;
   pub fn define_proof<K>(label: &str) -> Result<Prover<K>, ProofError>;
impl<K> Prover<K> {
    pub fn prove<S: Subjects>(&self, subjects: S) -> Result<Proof<K, S::Names>, ProofError>;
    pub fn verifier(&self) -> Verifier<K>;
}
```

Python API:

```python
def name(value): ...
def define_proof(kind): ...
def requires(**requirements): ...
```

Public verifier accepts proofs but cannot mint them. Python requirements name the
function's subject parameters and proof parameter; wrapper signature remains typed
through ParamSpec. Runtime authority is opaque and never serializable. A binding
owns language values, passes only name handles to the core, and checks authority
before invoking the consumer's operation. Additional adapters can reuse those exact
core types without parsing Python or TypeScript.

Call stack: consumer checker performs real I/O -> private issuer mints proof ->
sensitive-boundary wrapper binds arguments -> verifier checks issuer + ordered names ->
consumer operation. Denial ends before the operation. No database session, task, or
product-agent behavior changes.

## Slices

1. Rust core and one Python call end to end; verify identity mismatch in installed extension.
2. Typed Rust contracts, multiple proofs, sync/async decorators, scoped names, and trusted-module linting.
3. Docs, examples, type checks, packaging, CI, private repository upload and remote verification.

## Verification

- cargo fmt/clippy/test with locked dependencies, compile-fail fixtures for CA-3/4/5.
- Installed wheel tests exercise real protected writes for CA-1/2/3/4/5/6/9.
- Actual linter command against clean and violating modules for CA-8.
- Separate Rust consumer and clean Python environment test packaged artifacts for CA-10.
- gh API visibility and commit checks verify CA-10; never publish a public registry package.
- Run make check, build wheel and source archive, install the wheel into a fresh
  environment, and exercise the examples before pushing. Audit dependencies,
  exercise wrong-interface import rejection and panic containment, and pin exports.

## Plan review

Reviewed by rust-kit and backend-kit. Backend conventions do not apply outside
backend/. Applied Rust review: explicit seam, dependency decisions, manifest lint
baseline, opaque PyO3 contract, installed-artifact publication checks, precise
adapter claims, and verifier-bound issuer integrity. User authorization to port
and privately upload supersedes an additional plan approval step.

## Adoption skill cases

- "Add GDP proofs to a Python password API": create private checkers and a
  decorated sensitive function; verify a real write and wrong-project rejection.
- "Protect a Rust API": use generative names and invariant signatures; require
  the original verifier, and show a compiler failure for a different subject.
- "Add a binding in another language": link the plain runtime core, hide all
  constructors, and port the adapter acceptance and rejection cases.

The skill uses bundled Python, adapter, and guarantee references. No helper script
or generated template assets are needed; deterministic enforcement is gdp-lint.

## Completion evidence

Code revision c6ecae24d30b35be3bac6148fa6e52550edfef93 is uploaded to the private
cloudthinker-ai/gdp repository. GitHub Actions run 37342180432 completed successfully:
all four Python 3.11–3.14 jobs ran Rust contracts, 33 Python tests, packaging, and
clean-wheel tests; the advisory audit passed. Direct installation from that private
revision ran the real protected SQLite example. Additional Rust and Python consumers
followed the adoption skill successfully. See docs/verification.md.
