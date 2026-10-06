from types import TracebackType
from typing import Any, Generic, Never, TypeVar, TypeVarTuple, overload

T = TypeVar("T")
K = TypeVar("K")
Ts = TypeVarTuple("Ts")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")
T6 = TypeVar("T6")
T7 = TypeVar("T7")
T8 = TypeVar("T8")
INTERFACE_VERSION: int
__all__: list[str]

class AuthorizationError(PermissionError): ...

class Named(Generic[T]):
    def __init__(self, _unconstructible: Never) -> None: ...
    @property
    def value(self) -> T: ...
    def __repr__(self) -> str: ...

class Names(Generic[*Ts]):
    def __init__(self, _unconstructible: Never) -> None: ...
    def __enter__(self) -> tuple[*Ts]: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool: ...

class Proof(Generic[K]):
    def __init__(self, _unconstructible: Never) -> None: ...
    @property
    def kind(self) -> str: ...
    @property
    def evidence(self) -> object: ...
    def __repr__(self) -> str: ...

class ProofKind(Generic[K]):
    def __init__(self, _unconstructible: Never) -> None: ...
    @property
    def kind(self) -> str: ...
    def require(self, proof: Proof[K], *about: Named[Any]) -> None: ...

class Prover(Generic[K]):
    def __init__(self, _unconstructible: Never) -> None: ...
    @property
    def kind(self) -> ProofKind[K]: ...
    def prove(self, *about: Named[Any], evidence: object = None) -> Proof[K]: ...

def name(value: T) -> Named[T]: ...
@overload
def names() -> Names[()]: ...
@overload
def names(value1: T1, /) -> Names[Named[T1]]: ...
@overload
def names(value1: T1, value2: T2, /) -> Names[Named[T1], Named[T2]]: ...
@overload
def names(
    value1: T1, value2: T2, value3: T3, /
) -> Names[Named[T1], Named[T2], Named[T3]]: ...
@overload
def names(
    value1: T1, value2: T2, value3: T3, value4: T4, /
) -> Names[Named[T1], Named[T2], Named[T3], Named[T4]]: ...
@overload
def names(
    value1: T1, value2: T2, value3: T3, value4: T4, value5: T5, /
) -> Names[Named[T1], Named[T2], Named[T3], Named[T4], Named[T5]]: ...
@overload
def names(
    value1: T1, value2: T2, value3: T3, value4: T4, value5: T5, value6: T6, /
) -> Names[Named[T1], Named[T2], Named[T3], Named[T4], Named[T5], Named[T6]]: ...
@overload
def names(
    value1: T1,
    value2: T2,
    value3: T3,
    value4: T4,
    value5: T5,
    value6: T6,
    value7: T7,
    /,
) -> Names[
    Named[T1], Named[T2], Named[T3], Named[T4], Named[T5], Named[T6], Named[T7]
]: ...
@overload
def names(
    value1: T1,
    value2: T2,
    value3: T3,
    value4: T4,
    value5: T5,
    value6: T6,
    value7: T7,
    value8: T8,
    /,
) -> Names[
    Named[T1],
    Named[T2],
    Named[T3],
    Named[T4],
    Named[T5],
    Named[T6],
    Named[T7],
    Named[T8],
]: ...
@overload
def names(*values: object) -> Names[*tuple[Named[Any], ...]]: ...
@overload
def define_proof(kind: str, *, tag: type[K]) -> Prover[K]: ...
@overload
def define_proof(kind: str) -> Prover[Any]: ...
