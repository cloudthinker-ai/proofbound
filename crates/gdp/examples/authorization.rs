use gdp::runtime::ProofError;
use gdp::{Identity, Named, Proof, Prover, Verifier, define_proof, name2};

mod proofs {
    use super::{Identity, Named, Proof, ProofError, Prover, Verifier, define_proof};

    pub enum Admin {}

    pub type AdminProof<'u, 'p> = Proof<Admin, (Identity<'u>, Identity<'p>)>;

    pub struct Policy {
        issuer: Prover<Admin>,
    }

    impl Policy {
        pub fn new() -> Result<Self, ProofError> {
            Ok(Self {
                issuer: define_proof("ProjectAdmin")?,
            })
        }

        pub fn verifier(&self) -> Verifier<Admin> {
            self.issuer.verifier()
        }

        pub fn check<'u, 'p>(
            &self,
            user: &Named<'u, &str>,
            project: &Named<'p, &str>,
        ) -> Result<Option<AdminProof<'u, 'p>>, ProofError> {
            if *user.value() != "alice" || *project.value() != "p1" {
                return Ok(None);
            }
            self.issuer.prove((user, project)).map(Some)
        }
    }
}

fn change_password<'u, 'p>(
    policy: &Verifier<proofs::Admin>,
    user: &Named<'u, &str>,
    project: &Named<'p, &str>,
    proof: &Proof<proofs::Admin, (Identity<'u>, Identity<'p>)>,
    password: &mut String,
) -> Result<(), ProofError> {
    policy.require(proof, (user, project))?;
    *password = "new".into();
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let policy = proofs::Policy::new()?;
    let verifier = policy.verifier();
    let mut password = "old".to_owned();
    name2("alice", "p1", |user, project| -> Result<(), ProofError> {
        if let Some(proof) = policy.check(&user, &project)? {
            change_password(&verifier, &user, &project, &proof, &mut password)?;
        }
        Ok(())
    })?;
    assert_eq!(password, "new");
    Ok(())
}
