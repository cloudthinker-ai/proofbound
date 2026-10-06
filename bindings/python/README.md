# Proofbound for Python

Rust-backed authorization contracts. The extension creates opaque names and proofs;
the Python decorator checks them before a sensitive function runs.

Proofbound is an early project with an evolving API. The Python distribution is
`gdp-rs`, the import package is `gdp`, and the linter command is `gdp-lint`.

## Install

```bash
pip install gdp-rs==0.1.0
```

CPython 3.11–3.14 is tested. Release wheels support Linux x64/ARM64 (glibc 2.17+),
macOS ARM64 (11+) and Windows x64. Wheel installation does not require Rust;
building from source requires Rust 1.90 or newer.

## How it works

A trusted application module performs the real permission or entitlement check,
then issues a proof for named arguments. A sensitive function declares the proof
it requires using `@requires`. Before the body runs, Rust verifies the exact
issuer, ordered subject identities and active scope.

Equal raw IDs named separately have different identities. Type hints and the
AST linter add checks for accidental misuse. The library does not decide your
policy, prevent permission revocation or make a check and write atomic. Python
code running in the same process can bypass a decorator; this is not a sandbox.

See the [Python API](https://github.com/cloudthinker-ai/proofbound/blob/main/docs/python.md),
[guarantee matrix](https://github.com/cloudthinker-ai/proofbound/blob/main/docs/guarantees.md)
and [executable SQLite example](https://github.com/cloudthinker-ai/proofbound/tree/main/examples/python).
The [repository README](https://github.com/cloudthinker-ai/proofbound) includes
trusted checker and protected function examples.

## Attribution

Inspired by Guillermo Rauch's MIT-licensed
[gdp-ts](https://github.com/rauchg/gdp-ts), Matt Noonan's
[Ghosts of Departed Proofs](https://kataskeue.com/gdp.pdf), and Ollie Charles's
[Who Authorized These Ghosts!?](https://blog.ocharles.org.uk/posts/2019-08-09-who-authorized-these-ghosts.html).
The original copyright notice and MIT license are preserved in the distribution.
