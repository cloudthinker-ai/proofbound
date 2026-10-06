from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache, partial, wraps
from inspect import (
    Signature,
    isasyncgenfunction,
    iscoroutinefunction,
    isfunction,
    isgeneratorfunction,
    ismethod,
    signature,
)
from typing import Any, ParamSpec, TypeVar, cast

from ._gdp import AuthorizationError, Named, Proof, ProofKind

P = ParamSpec("P")
R = TypeVar("R")
_Reader = Callable[[tuple[object, ...], dict[str, object]], object]


@dataclass(frozen=True, slots=True)
class Requirement:
    kind: ProofKind[Any]
    subjects: tuple[str, ...]


def _compile_verifier(
    contract: Signature,
    requirements: dict[str, Requirement],
) -> Callable[[tuple[object, ...], dict[str, object]], None]:
    positional = (
        name
        for name, parameter in contract.parameters.items()
        if parameter.kind
        in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    )
    positions = {name: index for index, name in enumerate(positional)}

    @lru_cache(maxsize=128)
    def plan(
        count: int, keywords: tuple[str, ...]
    ) -> tuple[tuple[ProofKind[Any], _Reader, tuple[_Reader, ...]], ...]:
        contract.bind(*([None] * count), **dict.fromkeys(keywords))

        def reader(name: str) -> _Reader:
            if name in positions and positions[name] < count:
                index = positions[name]
                return lambda args, kwargs: args[index]
            if (
                name in keywords
                and contract.parameters[name].kind
                != contract.parameters[name].POSITIONAL_ONLY
            ):
                return lambda args, kwargs: kwargs[name]
            default = contract.parameters[name].default
            return lambda args, kwargs: default

        return tuple(
            (
                requirement.kind,
                reader(parameter),
                tuple(reader(subject) for subject in requirement.subjects),
            )
            for parameter, requirement in requirements.items()
        )

    def verify(args: tuple[object, ...], kwargs: dict[str, object]) -> None:
        for kind, proof_reader, subject_readers in plan(len(args), tuple(kwargs)):
            proof = proof_reader(args, kwargs)
            if not isinstance(proof, Proof):
                raise AuthorizationError(
                    "A real proof and named arguments are required"
                )
            subjects = []
            for reader in subject_readers:
                subject = reader(args, kwargs)
                if not isinstance(subject, Named):
                    raise AuthorizationError(
                        "A real proof and named arguments are required"
                    )
                subjects.append(subject)
            kind.require(proof, *subjects)

    return verify


def requires(**requirements: Requirement) -> Callable[[Callable[P, R]], Callable[P, R]]:
    if not requirements:
        raise ValueError("Declare at least one proof requirement")

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        target = function
        while isinstance(target, partial) and type(target) is partial:
            target = target.func
        if not (isfunction(target) or ismethod(target)):
            raise TypeError(
                "Proof contracts require Python functions, bound methods, "
                "or their partials"
            )
        if isinstance(function, partial):
            function = cast(
                Callable[P, R],
                partial(function.func, *function.args, **function.keywords),
            )
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

        verify = _compile_verifier(contract, requirements)

        if iscoroutinefunction(function):

            @wraps(function)
            async def async_checked(*args: P.args, **kwargs: P.kwargs) -> Any:
                verify(args, kwargs)
                return await function(*args, **kwargs)

            return cast(Callable[P, R], async_checked)

        @wraps(function)
        def checked(*args: P.args, **kwargs: P.kwargs) -> R:
            verify(args, kwargs)
            return function(*args, **kwargs)

        return checked

    return decorate
