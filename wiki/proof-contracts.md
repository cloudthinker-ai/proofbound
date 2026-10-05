---
type: concept
description: Proofs bind a checked fact to the exact values a sensitive operation consumes.
verified_at: 2026-10-05
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

## What Breaks

A faulty trusted checker can issue a faulty proof. A stale fact can outlive a
permission change. A path that bypasses the protected API is unprotected. The
library prevents omission and mixups at the boundaries that adopt it; it is not
a policy engine, transaction lock, proof assistant, or remote credential.
