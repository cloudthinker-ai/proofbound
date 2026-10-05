mod fault;
mod objects;

use gdp::runtime::ProofError;
use pyo3::exceptions::{PyPermissionError, PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyTuple;

use objects::{Named, Names, Proof, ProofKind, Prover};

pyo3::create_exception!(_gdp, AuthorizationError, PyPermissionError);

pub(super) fn contain_fault<T>(operation: impl FnOnce() -> PyResult<T>) -> PyResult<T> {
    fault::contain(operation)
        .map_err(|_| PyRuntimeError::new_err("Rust proof engine internal fault"))?
}

pub(super) fn authorization_error(error: ProofError) -> PyErr {
    AuthorizationError::new_err(error.to_string())
}

#[pyfunction]
fn name(value: Py<PyAny>) -> Named {
    Named::new(value, gdp::runtime::Name::fresh())
}

#[pyfunction]
#[pyo3(signature = (*values))]
fn names(values: &Bound<'_, PyTuple>) -> PyResult<Names> {
    contain_fault(|| Names::new(values))
}

#[pyfunction]
#[pyo3(signature = (kind, *, tag=None))]
fn define_proof(kind: &str, tag: Option<Py<PyAny>>) -> PyResult<Prover> {
    let _ = tag;
    contain_fault(|| {
        Ok(Prover::new(gdp::runtime::Prover::new(kind).map_err(
            |error| PyValueError::new_err(error.to_string()),
        )?))
    })
}

#[pymodule]
fn _gdp(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("INTERFACE_VERSION", 1)?;
    module.add(
        "AuthorizationError",
        module.py().get_type::<AuthorizationError>(),
    )?;
    module.add_class::<Named>()?;
    module.add_class::<Names>()?;
    module.add_class::<Proof>()?;
    module.add_class::<ProofKind>()?;
    module.add_class::<Prover>()?;
    module.add_function(wrap_pyfunction!(name, module)?)?;
    module.add_function(wrap_pyfunction!(names, module)?)?;
    module.add_function(wrap_pyfunction!(define_proof, module)?)?;
    module.add(
        "__all__",
        [
            "INTERFACE_VERSION",
            "AuthorizationError",
            "Named",
            "Names",
            "Proof",
            "ProofKind",
            "Prover",
            "name",
            "names",
            "define_proof",
        ],
    )?;
    Ok(())
}
