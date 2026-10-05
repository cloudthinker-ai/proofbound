from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from inspect import (
    Signature,
    isasyncgenfunction,
    iscoroutinefunction,
    isgeneratorfunction,
    signature,
)
from typing import Any, ParamSpec, TypeVar, cast

from ._gdp import AuthorizationError, Named, Proof, ProofKind

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True, slots=True)
class Requirement:
    kind: ProofKind[Any]
    subjects: tuple[str, ...]


def _verify(
    contract: Signature,
    requirements: dict[str, Requirement],
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> None:
    bound = contract.bind(*args, **kwargs)
    bound.apply_defaults()
    for parameter, requirement in requirements.items():
        proof = bound.arguments[parameter]
        subjects = [bound.arguments[subject] for subject in requirement.subjects]
        if not isinstance(proof, Proof) or any(
            not isinstance(subject, Named) for subject in subjects
        ):
            raise AuthorizationError("A real proof and named arguments are required")
        requirement.kind.require(proof, *subjects)


def requires(**requirements: Requirement) -> Callable[[Callable[P, R]], Callable[P, R]]:
    if not requirements:
        raise ValueError("Declare at least one proof requirement")

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        if isgeneratorfunction(function) or isasyncgenfunction(function):
            raise TypeError("Proof contracts require ordinary or async functions")
        contract = signature(function)
        for parameter, requirement in requirements.items():
            if not isinstance(requirement, Requirement):
                raise TypeError("Proof requirements must be Requirement objects")
            if not isinstance(requirement.kind, ProofKind):
                raise TypeError("Proof requirement kind must be a real ProofKind")
            if not isinstance(requirement.subjects, tuple) or any(
                not isinstance(subject, str) for subject in requirement.subjects
            ):
                raise TypeError("Proof subject parameters must be a tuple of names")
            for name in (parameter, *requirement.subjects):
                if name not in contract.parameters:
                    raise ValueError("Proof requirement refers to an unknown parameter")
                if contract.parameters[name].kind in (
                    contract.parameters[name].VAR_POSITIONAL,
                    contract.parameters[name].VAR_KEYWORD,
                ):
                    raise ValueError("Proof requirements must name explicit parameters")

        if iscoroutinefunction(function):

            @wraps(function)
            async def async_checked(*args: P.args, **kwargs: P.kwargs) -> Any:
                _verify(contract, requirements, args, kwargs)
                return await function(*args, **kwargs)

            return cast(Callable[P, R], async_checked)

        @wraps(function)
        def checked(*args: P.args, **kwargs: P.kwargs) -> R:
            _verify(contract, requirements, args, kwargs)
            return function(*args, **kwargs)

        return checked

    return decorate
