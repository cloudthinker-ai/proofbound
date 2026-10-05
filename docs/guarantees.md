# Proof guarantees

| Condition | Typed Rust | Python |
| --- | --- | --- |
| Missing required proof | Function signature fails compilation | Type hints flag omission; argument binding raises before the body |
| Wrong fact type | Invariant kind parameter fails compilation | Type hints distinguish tags; verifier rejects issuer mismatch |
| Wrong named user/project | Invariant generative identities fail compilation | Core rejects exact ordered identity mismatch |
| Same label, different issuer | Core verifier rejects it | Core verifier rejects it |
| Name/proof escapes callback | Generative lifetime fails compilation | Scoped names expire at context exit; unscoped `name` does not expire |
| Fake dictionary or direct constructor | Private fields prevent construction | Extension types reject construction, subclassing, and serialization |
| Issuer exported accidentally | Module review and verifier discipline | AST lint checks common export/minting mistakes |
| Incorrect policy checker | Not proven | Not proven |
| Revocation or mutation after check | Not proven | Not proven |
| Distributed credential | Not supported | Not supported |

Rust's higher-rank callbacks quantify over fresh lifetimes. Names and proof subject
parameters are invariant, so one lifetime cannot be widened to another. The tests
compile real invalid programs with rustc and require them to fail for contract
errors, rather than failing because a dependency is missing.

Rust verifiers are still important: an exported marker type does not itself prevent
another module constructing a new issuer for that marker. Only the original
issuer's verifier accepts its proofs. Sensitive functions must call that verifier
before doing work.

In Python, `@requires` preserves the wrapped callable's signature and verifies all
requirements before calling it. An async function is checked when its coroutine is
awaited, before its body begins. Generator and async-generator functions are refused
because their deferred execution would make a check at call time misleading.

A check is a snapshot, not a lock. Closing a scope prevents subsequent admission;
it does not cancel an operation admitted before the close. Concurrent close or
permission revocation between verification and a write remains a transaction or
application lifecycle concern. Use immutable IDs, keep proofs inside one request,
and use database locking/constraints when atomic check-and-write matters.

Proofs are not secrets or cryptographic certificates. Consumers already have code
execution in the process. They can bypass a Python decorator using `__wrapped__`,
perform raw SQL, use reflection, or expose the issuer. The library makes accidental
omission and argument mixups hard at the protected API boundary; it cannot turn
untrusted in-process code into a security principal.
