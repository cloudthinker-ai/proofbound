# Python API

The distribution is `gdp-rs`; the import package is `gdp`. CPython 3.11 or newer is
supported. Wheels use abi3 and are specific to operating system and architecture.

## Naming

`name(value) -> Named[T]` returns an unscoped, read-only wrapper with a fresh identity.
`.value` returns the original value without copying or deep freezing it. Do not
mutate objects that a proof is about; prefer immutable IDs.

`names(*values) -> Names` creates a one-use context manager. Its `__enter__` returns
a tuple of named values. All scopes close on normal or exceptional `__exit__`.
The same context cannot be entered twice. Use ordinary `with` inside an async
function, and await protected operations before leaving the block. Passing names
into a detached task that outlives the block causes later verification to fail.

## Defining and checking facts

`define_proof(kind, *, tag=None) -> Prover[K]` creates an issuer. The optional class
`tag` links a fact to a static type, such as `Proof[Admin]`; it does not change runtime
identity. Without a tag the static kind is `Any`. Keep each issuer in a private
module-level variable in `proofs/`.
Include `proofs/__init__.py` so imports and strict type checking resolve the package
consistently when the consumer is checked from outside its source directory.

`Prover.kind -> ProofKind[K]` returns a verifier for that exact issuer. Export it.
`Prover.prove(*named, evidence=None) -> Proof[K]` creates proof about the ordered
named arguments. Call it only after the actual policy check succeeds.
`Proof.kind -> str` gives the safe fact label. `Proof.evidence -> object` gives the
optional check result; like a named value, evidence is not deep-frozen.
`ProofKind.require(proof, *named) -> None` validates the issuer and exact subjects.

## Sensitive functions

`Requirement(kind, subjects)` pairs a real verifier with a tuple of function
parameter names. `@requires(admin=Requirement(Admin, ("user", "project")))` means
the argument `admin` must contain a valid proof about arguments `user`, `project`.
Keyword/default/positional binding uses the original function signature. All
requirements must succeed before the function runs. Unknown parameter names and
variadic subject parameters are rejected when the function is decorated.

Multiple requirements are AND. For an OR policy, let a trusted checker decide
which branch grants access and mint one explicit policy fact, or branch into
separately protected functions. Do not let callers choose whether a requirement
is checked. Synchronous and async functions are supported; generators are not.

Errors are `AuthorizationError` (a `PermissionError`) for rejected proofs or closed
scopes, `TypeError` for invalid argument/object shapes, and `ValueError` for invalid
definitions or contracts. No diagnostic includes named values or attached evidence.

## Static checks

The package ships `py.typed` and `_gdp.pyi`. A type checker can reject a missing proof
or a `Proof[Plan]` passed to an argument requiring `Proof[Admin]`. It cannot assign
a fresh compile-time type to every runtime ID; exact value relationships are
checked by Rust at runtime.

`gdp-lint path...` recursively checks Python source and exits 1 on a diagnostic:

| Code | Rule |
| --- | --- |
| GDP000 | Missing, unreadable, or invalid Python input |
| GDP001 | Define issuers only in a path component named `proofs` |
| GDP002 | Issuers belong in one private module-level variable |
| GDP003 | Call `.prove` only in trusted modules |
| GDP004 | Do not construct opaque objects directly |
| GDP005 | Do not cast into proof/authority types |
| GDP006 | Do not export issuers or import private issuers |

The linter understands direct and aliased GDP imports. It is a syntactic guard,
not whole-program analysis: dynamic imports, arbitrary alias chains, reflection,
and decorator bypasses still require review. `.prove` is reserved for trusted
modules in linted source; unrelated methods with that name can also be flagged.
Choose explicit application roots instead of linting dependencies or the SDK itself.

The extension is a required dependency. A missing or mismatched interface fails
at import with an installation message; no permissive Python fallback is used.
