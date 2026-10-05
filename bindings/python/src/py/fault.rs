use std::panic::{AssertUnwindSafe, catch_unwind};

#[derive(Debug, PartialEq, Eq)]
pub(super) struct Fault;

pub(super) fn contain<T>(operation: impl FnOnce() -> T) -> Result<T, Fault> {
    catch_unwind(AssertUnwindSafe(operation)).map_err(|_| Fault)
}

#[cfg(test)]
mod tests {
    use super::{Fault, contain};

    #[test]
    fn rust_faults_are_contained_without_their_payload() {
        assert_eq!(contain(|| 7), Ok(7));
        assert_eq!(contain(|| panic!("internal engine failure")), Err(Fault));
    }
}
