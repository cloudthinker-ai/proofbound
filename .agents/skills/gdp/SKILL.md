---
name: gdp
description: Use on "add GDP proofs", "protect a Python API", or "protect a Rust API" to bind checks to sensitive operations.
---
# GDP adoption

Use this when permission, entitlement, validation, or resource relationships must
reach a sensitive operation for the exact values that were checked.

1. Identify the operation and every entry point that can call it. Name the facts
   it needs, and keep existing policy decisions and error behavior.
2. In Python, create one private module-level issuer per fact in `proofs/`.
   Include its `__init__.py` package marker for imports and strict type checks.
   Export a typed checking function and the issuer's read-only verifier, never the
   issuer. In Rust, keep the issuer private in the policy module and export a
   verifier plus a checking function.
3. Perform the actual database or policy-engine check before minting a proof.
   Returning `None` is a denial; do not mint proof from a boolean supplied by a caller.
4. Make the sensitive Python function require typed proof arguments and add
   `@requires` requirements naming its exact subject parameters. Rust signatures
   carry `Proof<Kind, Names>` and call the trusted verifier before side effects.
5. Name raw immutable IDs once at the entry point. Prefer Python `with names(...)`
   and Rust generative callbacks. Keep authorized calls inside the scope.
6. Prove the boundary through a real operation. Verify missing proofs, wrong
   resources, same-label foreign issuers, and scope escape cannot cause a write.
7. Run the type checker and `gdp-lint` on Python consumer code. Keep policy modules
   small enough to review. Never cast, serialize, or recreate an authority handle.

Before editing Python read [references/python.md](references/python.md); for a Rust
consumer or new adapter read [references/adapters.md](references/adapters.md).
Read [references/guarantees.md](references/guarantees.md) before claiming safety.
Proofs describe check-time facts;
revocation, mutable values, and check/write races still need application transactions.
Python does not have Rust's generative lifetime guarantees. The implementation is
Rust-backed, but Python verifies exact relationships at runtime.
