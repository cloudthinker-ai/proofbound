# Language adapters

The Rust core is the shared implementation. It has no dependencies and does not
perform authorization I/O. The Python extension is one adapter over it. A new
binding links `crates/gdp` and implements the following contract in its language.

## Core contract

`gdp::runtime` exports:

| Type | Responsibility |
| --- | --- |
| `Scope` | Shared, thread-safe lifetime; `close()` invalidates all its names |
| `Name` | Opaque subject identity; copies preserve identity, fresh names never share it |
| `Prover` | Private issuer capability; `prove(&[Name])` creates opaque evidence |
| `Verifier` | Public consumer capability; checks a proof against issuer and ordered names |
| `Proof` | Opaque issued evidence; not reconstructible from a label or raw IDs |
| `ProofError` | Fixed, value-free failure reason |

Create a prover once per trusted policy module and export only the verifier.
Provers constructed with the same label still have different identities.
`Verifier::require` checks the issuer, subject limit, open scopes, arity, order,
and exact identity. Zero subjects are supported for global facts; such a proof
has no scope expiry. Proofs support up to 64 subjects. Labels are ASCII identifiers
of 1–128 bytes. These limits apply in every adapter.

## Binding requirements

1. Keep the language value in the adapter and give it one Rust `Name` handle.
   Naming an equal value again must allocate a fresh handle. Copying the same
   named object must preserve its handle.
2. Hide constructors and fields of named values, proofs, issuers, and verifiers.
   Do not let untrusted code build a handle from an integer, pointer, JSON, label,
   or serialized dictionary.
3. Route proof creation through the trusted issuer. Expose a read-only verifier
   without a method that can mint proofs. Keep policy I/O in the consumer.
4. Check `Verifier::require` for every required fact before the sensitive function
   runs. Binding type checks alone are insufficient in a dynamic language.
5. Return fixed errors without the subject value, serialized proof, or policy
   exception. Catch Rust unwinds before crossing the foreign-function boundary.
6. Give the binding an integer interface version and reject mismatched versions.
7. Implement the identity, different-issuer/same-label, arity, order, forged
   object, scope-close, and protected-side-effect tests in the new language.

Python uses PyO3 frozen, non-subclassable classes. Its wrappers retain the Python
value and evidence objects; only core handles cross into Rust verification.
The Python extension interface is version 1.

## What is portable

Bindings share implementation and semantics, not serialized authority. A proof
object belongs to one process and its issuer instance. A fresh process or a new
binding instance cannot reconstruct a proof from a string label. Passing authority
between languages inside an embedding host requires retaining the actual core
handle through a trusted adapter. Independent processes must perform their own
checks.

No C ABI, JavaScript SDK, WASM interface, HTTP server, or cross-process token format
ships in this version. A C ABI would require an explicitly reviewed ownership and
unsafe-code boundary; a serialized protocol would require a separate threat model.
