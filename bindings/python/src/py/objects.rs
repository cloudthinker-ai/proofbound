use std::sync::atomic::{AtomicBool, Ordering};

use gdp::runtime;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::pyclass::{PyTraverseError, PyVisit};
use pyo3::types::{PyTuple, PyType};

use super::{authorization_error, contain_fault};

#[pyclass(frozen, module = "gdp._gdp")]
pub(super) struct Named {
    value: Py<PyAny>,
    inner: runtime::Name,
}

impl Named {
    pub(super) fn new(value: Py<PyAny>, inner: runtime::Name) -> Self {
        Self { value, inner }
    }
}

#[pymethods]
impl Named {
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.value)
    }

    #[getter]
    fn value(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        self.inner.ensure_live().map_err(authorization_error)?;
        Ok(self.value.clone_ref(py))
    }

    fn __repr__(&self) -> &'static str {
        "Named(<opaque>)"
    }

    #[classmethod]
    fn __class_getitem__(cls: &Bound<'_, PyType>, item: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        generic_alias(cls, item)
    }
}

#[pyclass(frozen, module = "gdp._gdp")]
pub(super) struct Names {
    scope: runtime::Scope,
    values: Box<[Py<PyAny>]>,
    entered: AtomicBool,
}

impl Names {
    pub(super) fn new(values: &Bound<'_, PyTuple>) -> PyResult<Self> {
        if values.len() > runtime::MAX_SUBJECTS {
            return Err(PyValueError::new_err(
                runtime::ProofError::TooManySubjects.to_string(),
            ));
        }
        Ok(Self {
            scope: runtime::Scope::new(),
            values: values.iter().map(Bound::unbind).collect(),
            entered: AtomicBool::new(false),
        })
    }
}

#[pymethods]
impl Names {
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        for value in &self.values {
            visit.call(value)?;
        }
        Ok(())
    }

    #[classmethod]
    fn __class_getitem__(cls: &Bound<'_, PyType>, item: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        generic_alias(cls, item)
    }

    fn __enter__<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        contain_fault(|| {
            if self.entered.swap(true, Ordering::AcqRel) {
                return Err(PyValueError::new_err(
                    "A names scope can only be entered once",
                ));
            }
            self.scope.ensure_open().map_err(authorization_error)?;
            let values = self
                .values
                .iter()
                .map(|value| {
                    Py::new(
                        py,
                        Named::new(
                            value.clone_ref(py),
                            self.scope.name().map_err(authorization_error)?,
                        ),
                    )
                })
                .collect::<PyResult<Vec<_>>>()?;
            PyTuple::new(py, values)
        })
    }

    fn __exit__(
        &self,
        _exc_type: &Bound<'_, PyAny>,
        _exc_value: &Bound<'_, PyAny>,
        _traceback: &Bound<'_, PyAny>,
    ) -> bool {
        self.scope.close();
        false
    }
}

#[pyclass(frozen, module = "gdp._gdp")]
pub(super) struct Proof {
    inner: runtime::Proof,
    evidence: Option<Py<PyAny>>,
}

#[pymethods]
impl Proof {
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.evidence)
    }

    #[getter]
    fn kind(&self) -> &str {
        self.inner.kind()
    }

    #[getter]
    fn evidence(&self, py: Python<'_>) -> Option<Py<PyAny>> {
        self.evidence
            .as_ref()
            .map(|evidence| evidence.clone_ref(py))
    }

    fn __repr__(&self) -> String {
        format!("Proof({})", self.inner.kind())
    }

    #[classmethod]
    fn __class_getitem__(cls: &Bound<'_, PyType>, item: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        generic_alias(cls, item)
    }
}

#[pyclass(frozen, module = "gdp._gdp")]
pub(super) struct Prover {
    inner: runtime::Prover,
}

impl Prover {
    pub(super) fn new(inner: runtime::Prover) -> Self {
        Self { inner }
    }
}

#[pymethods]
impl Prover {
    #[getter]
    fn kind(&self) -> ProofKind {
        ProofKind {
            inner: self.inner.verifier(),
        }
    }

    #[pyo3(signature = (*about, evidence=None))]
    fn prove(&self, about: &Bound<'_, PyTuple>, evidence: Option<Py<PyAny>>) -> PyResult<Proof> {
        contain_fault(|| {
            Ok(Proof {
                inner: self
                    .inner
                    .prove(&handles(about)?)
                    .map_err(authorization_error)?,
                evidence,
            })
        })
    }

    #[classmethod]
    fn __class_getitem__(cls: &Bound<'_, PyType>, item: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        generic_alias(cls, item)
    }
}

#[pyclass(frozen, module = "gdp._gdp")]
pub(super) struct ProofKind {
    inner: runtime::Verifier,
}

#[pymethods]
impl ProofKind {
    #[getter]
    fn kind(&self) -> &str {
        self.inner.kind()
    }

    #[pyo3(signature = (proof, *about))]
    fn require(&self, proof: PyRef<'_, Proof>, about: &Bound<'_, PyTuple>) -> PyResult<()> {
        contain_fault(|| {
            self.inner
                .require(&proof.inner, &handles(about)?)
                .map_err(authorization_error)
        })
    }

    #[classmethod]
    fn __class_getitem__(cls: &Bound<'_, PyType>, item: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        generic_alias(cls, item)
    }
}

fn handles(about: &Bound<'_, PyTuple>) -> PyResult<Vec<runtime::Name>> {
    if about.len() > runtime::MAX_SUBJECTS {
        return Err(authorization_error(runtime::ProofError::TooManySubjects));
    }
    about
        .iter()
        .map(|value| {
            value
                .extract::<PyRef<'_, Named>>()
                .map(|value| value.inner.clone())
                .map_err(Into::into)
        })
        .collect()
}

fn generic_alias(cls: &Bound<'_, PyType>, item: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    Ok(cls
        .py()
        .import("types")?
        .getattr("GenericAlias")?
        .call1((cls, item))?
        .unbind())
}
