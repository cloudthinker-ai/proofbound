# Python adoption improvements

## Problem

Python reference cycles through immutable extension handles are invisible to GC.
Scoped naming erases payload types. Lint misses explicit decorator bypasses and
relative private issuer imports. Consumer checks cover mypy only, and wheels are
built only for one Linux architecture.

## Repo conventions to follow

The standalone Proofbound AGENTS.md governs this repository. Keep all PyO3 code
in bindings/python/src/py/, all handles frozen, interface version 1 and package
names unchanged. Match existing pytest public-contract tests, preserve identical
licenses, and keep the plain Rust core unchanged. No backend integration or
registry publication is part of this task.

## Case Analysis

- CA-GC: Python value/evidence/scope -> handle -> Python cycle is collected;
  reachable handles remain usable. Immutable Rust references are traversed, never
  mutated by GC. No additional locks or authority invalidation are required.
- CA-TYPES: 0–8 scoped values retain ordered Named payload types and tuple length;
  larger/dynamic arities retain a documented Any fallback. Wrong payload methods,
  wrong proof kinds, omitted proofs, and wrong tuple unpacking fail type checks.
- CA-LINT: direct or aliased __wrapped__ access and inspect.unwrap of protected
  callables are lint errors. Relative private issuer imports resolve from the
  source package; unrelated relative imports stay valid. This remains syntactic
  checking, not an in-process security sandbox.
- CA-HTTP: a FastAPI dependency yields named IDs in a request scope, the trusted
  checker grants admin proof, and a protected async use case updates real SQLite.
  Wrong issuer/subject and closed scopes yield HTTP 403 with no write; the next
  request succeeds and earlier request authority expires after response.
- CA-WHEEL: CPython 3.11–3.14 checks keep passing; native Linux x64/ARM64,
  macOS ARM64, and Windows x64 jobs build abi3 wheels and test fresh installations
  without Rust at install time. Artifacts remain in the private repository.

## Program Design

- Edit objects.rs: __traverse__ visits every immutable owned Python reference;
  Names also exposes __class_getitem__ for its generic stub contract.
- Edit _gdp.pyi: variadic Names[*Ts], __enter__ -> tuple[*Ts], names overloads
  for 0–8 values plus dynamic fallback. No Python wrapper around Rust handles.
- Edit lint.py: GDP007 for __wrapped__/inspect.unwrap; resolve relative imports
  before private-issuer checks. Existing diagnostics remain value-free.
- Edit existing contract, typing, lint tests; add one FastAPI/SQLite integration
  test in tests/proofs/ so trusted issuer placement follows the lint contract.
- Edit test dependencies and make targets: pinned FastAPI/httpx/Pyrefly for
  consumer tests, Pyrefly source checking beside mypy.
- Edit ci.yml: platform wheel jobs using pinned maturin-action, pinned toolchain,
  manylinux2014 on Linux; verify wheel tags/licenses/types before upload.
- Edit docs/python.md, README.md, wiki/proof-contracts.md and AGENTS.md to document
  guarantees, scoped typing limits, lint rules and private wheel installation.

No new runtime Python or Rust dependency, no permissive fallback, no registry
release or repository visibility change. User explicitly authorized implementation,
commit and push; proceed without another design approval pause.

## Slices

1. Add GC/type/lint regressions and prove they fail on the current code, then
   implement each fix and run its focused tests.
2. Add HTTP dependency lifecycle/SQLite tests and Pyrefly checks; prove the
   integration and type contract on both editable and installed packages.
3. Build/test private platform wheels in CI, document the supported targets,
   run make check/package-check and installed-wheel verification, then commit/push
   and inspect hosted results; fix any platform failures before completion.

## Review refinements

Reviewed by rust-kit and design-kit/Python consumer reviewers. The implementation
applies their concrete clarification requests below; no further user approval is
needed because this turn explicitly authorized implementation and push.

### Paths and recovery

Happy: request -> shared scoped identities -> SQLite policy check -> protected
async write -> HTTP 200 -> dependency teardown. Denied checks and rejected proofs
produce a value-free HTTP 403 and unchanged rows; callers obtain fresh authorization
in a new request. A stale post-response proof raises AuthorizationError. Type and
lint failures are actionable CI diagnostics; correct the payload operation or use
public checker/verifier imports. An incompatible wheel fails before testing;
select the matching artifact or build from source on an unsupported platform.

Assumptions challenged: an abi3 wheel is not architecture-independent; a passing
mypy check alone does not prove Pyrefly compatibility; immutable wrapper fields
still own Python references; arbitrary-sized argument lists cannot retain fixed
ordered types in Python 3.11. Engineer flags: no mutation or locks during traversal,
no authorization after request cleanup. Consumer flags: install without Rust,
clear HTTP errors, no exposed payload or evidence in errors. No product UI changes.

### Exact signatures and semantics

`Names[*Ts]` uses already-wrapped element types, not raw payload types. Overloads
return `Names[Named[T1], Named[T2], ...]`; `__enter__ -> tuple[*Ts]` therefore
returns the real Named objects. The 0-argument result is `Names[()]`; the dynamic
fallback is `Names[*tuple[Named[Any], ...]]`. This preserves a single opaque runtime
class rather than inventing eight new exported classes. Mypy and Pyrefly verify
0, 1, 2, 8, 9, and dynamic arities, payload methods, tuple unpacking, wrong proof
kinds, and missing proofs. Existing consumer proofs/__init__.py guidance remains.

`Named.__traverse__(visit)` visits Named.value once; Names visits each element of
Names.values; Proof visits optional Proof.evidence. Prover and ProofKind own no
Python references. All bodies only visit references. No Python attachment,
getters, scope checks, copying, or locks. Omit __clear__ because these references
are immutable; every cycle contains a mutable Python reference that GC can clear.
Tests check reachable handle usability and collection for all three owning types,
including scoped Named; the supported wheels target ordinary CPython, not the
free-threaded ABI.

The lint AST visitor resolves ImportFrom.level by walking level-1 parents from
source.parent, then appending module components. A target with a proofs component
rejects private and star imports; unrelated .helpers is valid. GDP007 rejects
.__wrapped__ access including assignment, inspect.unwrap, aliased unwrap imports,
and inspect module aliases. It reserves these syntactic operations even on other
decorators; unrelated obj.unwrap passes. getattr/reflection remain review concerns.

HTTP call stack:
PUT /projects/{project}/password -> yielding subjects dependency enters names ->
checked_admin reads SQLite membership -> route awaits change_password -> requires
verifies issuer/subjects/scope -> UPDATE + commit -> route returns -> scope closes.
The route maps AuthorizationError to a fixed HTTP 403 message; a dedicated global
exception handler is not required. Wrong-issuer/subject/expired fixtures are
produced by a test-only trusted dependency. No database or HTTP mocks.

### Files and test checkpoints

| Action | File | Case / observable result |
| --- | --- | --- |
| edit | bindings/python/src/py/objects.rs | CA-GC and runtime Names generic alias |
| edit | bindings/python/python/gdp/_gdp.pyi | CA-TYPES exact ordered named elements |
| edit | bindings/python/python/gdp/lint.py | CA-LINT GDP006/GDP007 diagnostics |
| edit | bindings/python/tests/proofs/test_contracts.py | CA-GC cycles reclaimed, reachable handles usable |
| edit | bindings/python/tests/test_typing.py | CA-TYPES both checkers reject 5 invalid contracts |
| edit | bindings/python/tests/test_lint.py | CA-LINT rejects bypass/relative leaks; unrelated forms pass |
| new | bindings/python/tests/proofs/test_fastapi.py | CA-HTTP 200/write; 403/no write; closed old scope; next request succeeds |
| new | scripts/test_wheel.py | CA-WHEEL tags, metadata, binary-only fresh install, all contract tests |
| edit | scripts/check_artifacts.py | CA-WHEEL shared packaged license/type/API validation |
| edit | requirements-dev.txt, bindings/python/pyproject.toml, Makefile | development-only FastAPI/httpx2/Pyrefly |
| edit | .github/workflows/ci.yml | CA-WHEEL all four platform artifacts on Python 3.11–3.14 |
| edit | AGENTS.md, README.md, docs/python.md, wiki/proof-contracts.md | public guarantees and adoption instructions |

Regressions were proven on the old binding: four GC failures, four bypass forms,
one relative-import failure, and scoped-type assertions. Preserve the existing
forgery, issuer, identity, order, arity, closure, sync/async, and SQLite guard tests.

Wheel jobs use ubuntu-24.04/x86_64-unknown-linux-gnu,
ubuntu-24.04-arm/aarch64-unknown-linux-gnu with manylinux2014 containers;
macos-14/aarch64-apple-darwin; windows-2022/x86_64-pc-windows-msvc.
Pin maturin-action e83996d129638aa358a18fbd1dfb82f0b0fb5d3b,
maturin 1.14.1 and Rust 1.90.0. Assert cp311-abi3 and platform filename tags,
license, stubs and metadata. For each wheel, create independent environments on
3.11–3.14, binary-only install wheel/development dependencies, verify installed
import location, run all Python contracts (including both checkers, HTTP and
interface version), lint and SQLite example. Only tested wheels are uploaded to
private Actions artifacts; no registry or public release.
