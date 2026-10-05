use std::fmt;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};

pub const MAX_SUBJECTS: usize = 64;
pub const MAX_KIND_BYTES: usize = 128;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProofError {
    InvalidKind,
    TooManySubjects,
    ClosedScope,
    WrongKind,
    WrongSubjects,
}

impl fmt::Display for ProofError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::InvalidKind => {
                "Proof kind must be a nonempty ASCII identifier of at most 128 bytes"
            }
            Self::TooManySubjects => "A proof supports at most 64 subjects",
            Self::ClosedScope => "Named values are outside their active scope",
            Self::WrongKind => "Proof was not issued by the required authority",
            Self::WrongSubjects => "Proof does not match the exact ordered named arguments",
        })
    }
}

impl std::error::Error for ProofError {}

#[derive(Clone, Default)]
pub struct Scope {
    closed: Arc<AtomicBool>,
}

impl Scope {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn name(&self) -> Result<Name, ProofError> {
        self.ensure_open()?;
        Ok(Name {
            identity: Arc::new(()),
            scope: self.clone(),
        })
    }

    pub fn close(&self) {
        self.closed.store(true, Ordering::Release);
    }

    pub fn ensure_open(&self) -> Result<(), ProofError> {
        if self.closed.load(Ordering::Acquire) {
            Err(ProofError::ClosedScope)
        } else {
            Ok(())
        }
    }
}

#[derive(Clone)]
pub struct Name {
    identity: Arc<()>,
    scope: Scope,
}

impl Name {
    pub fn fresh() -> Self {
        Self {
            identity: Arc::new(()),
            scope: Scope::new(),
        }
    }

    pub fn ensure_live(&self) -> Result<(), ProofError> {
        self.scope.ensure_open()
    }

    fn is_same(&self, other: &Self) -> bool {
        Arc::ptr_eq(&self.identity, &other.identity)
    }
}

struct Definition {
    kind: Box<str>,
}

pub struct Prover {
    definition: Arc<Definition>,
}

#[derive(Clone)]
pub struct Verifier {
    definition: Arc<Definition>,
}

#[derive(Clone)]
pub struct Proof {
    definition: Arc<Definition>,
    subjects: Box<[Name]>,
}

impl Prover {
    pub fn new(kind: &str) -> Result<Self, ProofError> {
        if kind.is_empty()
            || kind.len() > MAX_KIND_BYTES
            || !kind
                .bytes()
                .enumerate()
                .all(|(i, b)| b.is_ascii_alphabetic() || b == b'_' || (i > 0 && b.is_ascii_digit()))
        {
            return Err(ProofError::InvalidKind);
        }
        Ok(Self {
            definition: Arc::new(Definition { kind: kind.into() }),
        })
    }

    pub fn verifier(&self) -> Verifier {
        Verifier {
            definition: Arc::clone(&self.definition),
        }
    }

    pub fn prove(&self, subjects: &[Name]) -> Result<Proof, ProofError> {
        validate_subjects(subjects)?;
        Ok(Proof {
            definition: Arc::clone(&self.definition),
            subjects: subjects.into(),
        })
    }
}

impl Verifier {
    pub fn kind(&self) -> &str {
        &self.definition.kind
    }

    pub fn require(&self, proof: &Proof, subjects: &[Name]) -> Result<(), ProofError> {
        if !Arc::ptr_eq(&self.definition, &proof.definition) {
            return Err(ProofError::WrongKind);
        }
        validate_subjects(subjects)?;
        validate_subjects(&proof.subjects)?;
        if proof.subjects.len() != subjects.len()
            || !proof
                .subjects
                .iter()
                .zip(subjects)
                .all(|(a, b)| a.is_same(b))
        {
            return Err(ProofError::WrongSubjects);
        }
        Ok(())
    }
}

impl Proof {
    pub fn kind(&self) -> &str {
        &self.definition.kind
    }
}

fn validate_subjects(subjects: &[Name]) -> Result<(), ProofError> {
    if subjects.len() > MAX_SUBJECTS {
        return Err(ProofError::TooManySubjects);
    }
    subjects.iter().try_for_each(Name::ensure_live)
}
