---
type: concept
description: Proofs bind a checked fact to the exact values a sensitive operation consumes.
verified_at: 2026-10-06
---
# Proof contracts

Alice may administer project A. That fact must not authorize changing project B,
even if both IDs are strings or one caller accidentally copies the wrong ID.
A proof contract names values, checks a fact about those names, and requires the
result at the sensitive boundary.

## Product Contract

The application owns its policy. GDP connects the checked decision to the operation
without deciding who counts as an administrator or which subscription is entitled.
A sensitive operation accepts only evidence from its trusted issuer about its
exact ordered subjects. Equal raw values named separately have different identities.

## Runtime Boundary

Rust can express fresh identity through invariant generative lifetimes. Dynamic
languages preserve the relationship through opaque Rust handles and verification
before side effects. Python is the first binding. Additional language adapters use
the same core contract without rewriting policy or verification.

The Python adapter preserves scoped payload types for up to eight arguments and
participates in cyclic garbage collection without mutating authority. Both mypy
and Pyrefly check installed consumers. A FastAPI dependency shares names within a
request; a protected use case verifies the proof before a database write, and
request teardown expires those names. Public platform wheels install without a
Rust toolchain. See the [Python API](../docs/python.md) for boundaries and limits.

Protected calls reuse a bounded cache of argument layouts without retaining
request values or authorization decisions. Each call verifies its own proof and
live subjects. The linter preserves diagnostics while building parent maps on
demand and pruning excluded dependency directories. Release-build comparisons
and their scope are described in [performance measurement](../docs/performance.md).
Decorated boundaries accept functions, bound methods and their partials; callable
instances are rejected so deferred execution cannot be misclassified as synchronous.
Source-directory traversal errors fail the lint command rather than silently
passing an incomplete scan. See the [0.1.1 security patch](../docs/releases/0.1.1.md).

The [Rust and gdp-ts comparison](../docs/core-performance.md) measures runtime
overhead separately from TypeScript's compile-time guarantees. Reusing a phantom
proof token and verifying opaque runtime identities perform different work;
benchmark output parity does not imply equivalent guarantees.

## What Breaks

A faulty trusted checker can issue a faulty proof. A stale fact can outlive a
permission change. A path that bypasses the protected API is unprotected. The
library prevents omission and mixups at the boundaries that adopt it; it is not
a policy engine, transaction lock, proof assistant, or remote credential.
