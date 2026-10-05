try:
    from . import _gdp
except ImportError as error:
    raise ImportError(
        "GDP extension is missing; install gdp-rs or run make install"
    ) from error

if _gdp.INTERFACE_VERSION != 1:
    raise ImportError("Incompatible GDP extension; reinstall gdp-rs")

from ._gdp import (
    AuthorizationError,
    Named,
    Names,
    Proof,
    ProofKind,
    Prover,
    define_proof,
    name,
    names,
)
from .contracts import Requirement, requires

__all__ = [
    "AuthorizationError",
    "Named",
    "Names",
    "Proof",
    "ProofKind",
    "Prover",
    "Requirement",
    "define_proof",
    "name",
    "names",
    "requires",
]
