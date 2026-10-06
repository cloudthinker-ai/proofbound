# Proofbound

Rust proof contracts with language adapters; Python is the first adapter.

## Boundaries
### ALWAYS
- Keep authorization decisions in consumer-owned trusted proof modules.
- Keep core logic dependency-free and adapters thin; only `bindings/python/src/py/` imports PyO3.
- Require exact issuer and ordered subject identities at every dynamic-language sensitive boundary.
- Preserve upstream attribution; describe compile-time and runtime guarantees separately.
- Keep the root and both packaged LICENSE files identical.
- Run `make check` and test an installed wheel before publishing.
- Traverse every Python reference owned by frozen handles; never mutate their authority for GC.
- Keep scoped payload types through eight arguments and check consumers with mypy and Pyrefly.
- Write no code comments; explain guarantees and limits in `docs/`.
### NEVER
- Serialize authority, accept proof-shaped dictionaries, or export a trusted issuer from an example.
- Use unsafe Rust or log subject values in diagnostics.
### ASK FIRST
- Publish publicly, change repository visibility, or publish a registry release.

## Architecture
- `crates/gdp/` owns scoped typed names and language-independent opaque handles.
- `bindings/python/` owns PyO3 classes, the Python API, lint command, and type declarations.
- `examples/` exercises real permission checks and protected operations.
- CI tests FastAPI request scopes and private wheels for Linux x64/ARM64, macOS ARM64 and Windows x64.
