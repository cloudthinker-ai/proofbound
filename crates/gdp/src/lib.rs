#![deny(clippy::print_stdout, clippy::print_stderr)]

pub mod runtime;
mod typed;

pub use typed::{
    Identity, Named, Proof, Prover, Subjects, Verifier, define_proof, name, name2, name3,
};
