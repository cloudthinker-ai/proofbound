# Proofbound

Sensitive functions require evidence that checks succeeded for their exact arguments.
This is a Rust rewrite of [gdp-ts](https://github.com/rauchg/gdp-ts), with a dependency-free
core and Python as the first language binding.

The repository is named Proofbound. The Rust crate `gdp`, Python distribution
`gdp-rs`, import package `gdp`, and command `gdp-lint` retain their existing names.

| Consumer | Enforcement |
| --- | --- |
| Rust | Generative names and invariant proof types reject missing or mismatched proofs at compile time; verifier checks also bind proofs to their issuer |
| Python | Rust creates opaque objects; a decorator verifies issuer, exact ordered names, and active scope before the function runs; type hints and lint add static checks |
| Additional languages | Add a thin binding over `gdp::runtime`; no authorization logic needs to be rewritten |

This library connects a decision to the operation that needs it. Your existing database,
policy engine, authentication, and entitlement checks still decide who may do what.

## Python

Build locally with Rust 1.90+, CPython 3.11+, and uv:

```bash
make install
.venv/bin/python examples/python/main.py
```

Install directly from the private repository using an authenticated Git credential helper:

```bash
uv pip install 'gdp-rs @ git+https://github.com/cloudthinker-ai/proofbound.git#subdirectory=bindings/python'
```

Source installs require Rust. `make wheel` builds an abi3 wheel for the current platform
that installs without a Rust toolchain. No package has been published to PyPI.

Private CI also builds tested wheels for Linux x64/ARM64 (glibc 2.17+), macOS ARM64
(11+), and Windows x64. Download the artifact for your platform from a successful
[Actions run](https://github.com/cloudthinker-ai/proofbound/actions), then install
its wheel. For example, on Linux x64, using the run ID of the commit you want:

```bash
gh run download RUN_ID --repo cloudthinker-ai/proofbound \
  --name proofbound-wheel-linux-x64 --dir wheels
uv pip install wheels/*.whl
```

The artifacts require access to the private repository. Each wheel uses CPython's
3.11 stable ABI; CI checks Python 3.11–3.14. Use source installation for platforms
outside the wheel matrix.

Create the issuer inside a trusted module, keep it private, and export its verifier:

```python
from gdp import Named, Proof, define_proof

class Admin:
    pass

_issuer = define_proof("ProjectAdmin", tag=Admin)
ProjectAdmin = _issuer.kind

async def check_admin(user: Named[str], project: Named[str]) -> Proof[Admin] | None:
    allowed = await policy.is_admin(user.value, project.value)
    return _issuer.prove(user, project) if allowed else None
```

Declare the proof and the argument names it must cover at the sensitive boundary:

```python
from gdp import Named, Proof, Requirement, requires
from proofs.admin import Admin, ProjectAdmin

@requires(admin=Requirement(ProjectAdmin, ("user", "project")))
async def change_password(
    user: Named[str], project: Named[str], password: str, *, admin: Proof[Admin]
) -> None:
    await database.update_password(project.value, password)
```

Name the actual IDs once and pass those objects through both steps:

```python
from gdp import names

with names(user_id, project_id) as (user, project):
    admin = await check_admin(user, project)
    if admin is None:
        raise PermissionError("Project administrator access is required")
    await change_password(user, project, password, admin=admin)
```

The synchronous API is identical. Multiple keyword requirements enforce role AND
entitlement; the [SQLite example](examples/python/main.py) demonstrates both.
`AuthorizationError` subclasses `PermissionError`. Once the `with` block exits, its
names and proofs cannot be used to authorize another operation. `name(value)` is the
unscoped form for callers that deliberately manage lifetimes themselves.
Scoped naming preserves the ordered payload types for up to eight arguments;
names and evidence also support Python cyclic garbage collection.

```bash
.venv/bin/gdp-lint examples/python
```

`gdp-lint` checks accidental minting/export outside trusted `proofs/` modules,
direct opaque constructors, proof casts, and explicit decorator bypasses.
See [the lint contract](docs/python.md).

## Rust

Depend on the core without pulling in Python:

```toml
[dependencies]
gdp = { git = "https://github.com/cloudthinker-ai/proofbound", package = "gdp" }
```

```rust
use gdp::{define_proof, name2};

enum Admin {}

fn main() -> Result<(), gdp::runtime::ProofError> {
    let issuer = define_proof::<Admin>("ProjectAdmin")?;
    let verifier = issuer.verifier();
    name2("alice", "project", |user, project| {
        let proof = issuer.prove((&user, &project))?;
        verifier.require(&proof, (&user, &project))
    })
}
```

In real code the issuer belongs in the module that checks the policy, as in
[`authorization.rs`](crates/gdp/examples/authorization.rs). `Named::value()` borrows
the underlying value. Proof types include the identities of all their subjects.
Renaming even an equal raw ID produces a different identity. `name`, `name2`, and
`name3` keep names and proofs inside their callback. Additional arities compose
nested names and tuples.

## Guarantees and limits

- A proof is bound to a specific issuer, not just its text label or Rust marker.
- Proof subject identity is ordered and exact; equal values do not imply equal names.
- Python cannot construct or subclass opaque objects or turn a dictionary into a proof.
- Python's type hints cannot express Rust's fresh lifetimes; runtime checks are required.
- A proof records a fact at check time. Mutable values, permission revocation, and
  check/write races still need transactions or constraints in your application.
- Application code must protect every sensitive path. Raw SQL access, calling a
  decorated function's `__wrapped__`, or exporting an issuer bypasses the intended API.
- This is not a theorem prover, an in-process sandbox, or a network credential format.

See [the guarantee matrix](docs/guarantees.md), [Python API](docs/python.md), and
[adapter contract](docs/adapters.md). Rust and Python are implemented; other adapters
are extension points, not shipped SDKs.

## Verification

```bash
make install
make check
make audit
make package-check
```

Checks cover compiler rejection, real SQLite writes through sync and async functions,
forged and wrong-subject proofs, expired scopes, cross-thread close, lint diagnostics,
installed type hints, interface compatibility, and extension/stub agreement.
They also cover cyclic garbage collection, mypy and Pyrefly consumers, and a
FastAPI request lifecycle with real SQLite writes. CI exercises Python 3.11–3.14,
builds the source distribution and platform wheels, and tests fresh wheel installations.

## Attribution

Based on Guillermo Rauch's MIT-licensed [gdp-ts](https://github.com/rauchg/gdp-ts),
source revision `ebd0af9cae423997a43a024dc6d6738b0895bbec`. The original idea is Matt
Noonan's [Ghosts of Departed Proofs](https://kataskeue.com/gdp.pdf), with authorization
applications explored by Ollie Charles in
[Who Authorized These Ghosts!?](https://blog.ocharles.org.uk/posts/2019-08-09-who-authorized-these-ghosts.html).
The upstream license is preserved in [LICENSE](LICENSE).
