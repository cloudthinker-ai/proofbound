# Rust consumer recipe

Add a dependency on the private repository using the consumer's authenticated Git
credential helper, or use a path to the core in a local checkout:

```toml
[dependencies]
gdp = { git = "https://github.com/cloudthinker-ai/proofbound", package = "gdp" }
```

The core has no dependencies on Python. Keep a private issuer field in the policy
module. Give the operation the original policy verifier; accepting a marker type
alone does not prevent a new issuer with the same marker or label.

```rust
use gdp::{Identity, Named, Proof, Prover, Verifier, define_proof, name2};
use gdp::runtime::ProofError;

mod policy {
    use super::*;
    pub enum Admin {}
    pub type AdminProof<'u, 'p> = Proof<Admin, (Identity<'u>, Identity<'p>)>;
    pub struct Policy { issuer: Prover<Admin> }

    impl Policy {
        pub fn new() -> Result<Self, ProofError> {
            Ok(Self { issuer: define_proof("ProjectAdmin")? })
        }
        pub fn verifier(&self) -> Verifier<Admin> { self.issuer.verifier() }
        pub fn check<'u, 'p>(
            &self, user: &Named<'u, &str>, project: &Named<'p, &str>
        ) -> Result<Option<AdminProof<'u, 'p>>, ProofError> {
            if *user.value() != "alice" || *project.value() != "p1" {
                return Ok(None);
            }
            self.issuer.prove((user, project)).map(Some)
        }
    }
}

fn protected<'u, 'p>(
    verifier: &Verifier<policy::Admin>,
    user: &Named<'u, &str>, project: &Named<'p, &str>,
    proof: &policy::AdminProof<'u, 'p>, writes: &mut usize,
) -> Result<(), ProofError> {
    verifier.require(proof, (user, project))?;
    *writes += 1;
    Ok(())
}

fn main() -> Result<(), ProofError> {
    let policy = policy::Policy::new()?;
    let verifier = policy.verifier();
    let mut writes = 0;
    name2("alice", "p1", |user, project| -> Result<(), ProofError> {
        if let Some(proof) = policy.check(&user, &project)? {
            protected(&verifier, &user, &project, &proof, &mut writes)?;
        }
        Ok(())
    })?;
    assert_eq!(writes, 1);
    Ok(())
}
```

Replace the example policy with the real consumer's check; do not mint proofs from
caller-provided booleans. Run cargo check, cargo test, cargo run, and cargo clippy.

Required verification:

| Case | Expected boundary |
| --- | --- |
| Allowed check | One real protected operation succeeds |
| Denied check | No proof and no protected side effect |
| Missing proof | Compilation fails on the protected call |
| Wrong named subject or wrong fact marker | Compilation fails on invariant types/lifetimes |
| Return a name or proof from its callback | Compilation fails on lifetime escape |
| New issuer using the same label AND marker | Original verifier returns WrongKind, no side effect |
| Dynamic binding order/arity mismatch | Runtime core returns WrongSubjects |

Place negative programs in compile-fail fixtures. Invoke rustc or cargo check and
assert the expected contract diagnostic, not merely a nonzero status caused by a
missing crate. A local path dependency can run with CARGO_NET_OFFLINE=true and a
locked consumer manifest once generated.
