from __future__ import annotations

import asyncio
import pickle
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from inspect import signature

import pytest
from gdp import (
    AuthorizationError,
    Named,
    Names,
    Proof,
    ProofKind,
    Prover,
    Requirement,
    define_proof,
    name,
    names,
    requires,
)


class Admin:
    pass


class Entitled:
    pass


_admin = define_proof("Admin", tag=Admin)
_plan = define_proof("Plan", tag=Entitled)
_impostor = define_proof("Admin", tag=Admin)


@requires(
    admin=Requirement(_admin.kind, ("user", "project")),
    plan=Requirement(_plan.kind, ("project",)),
)
def write(
    db: sqlite3.Connection,
    user: Named[str],
    project: Named[str],
    password: str,
    *,
    admin: Proof[Admin],
    plan: Proof[Entitled],
) -> int:
    return db.execute(
        "UPDATE project SET password=? WHERE id=?", (password, project.value)
    ).rowcount


@requires(
    admin=Requirement(_admin.kind, ("user", "project")),
    plan=Requirement(_plan.kind, ("project",)),
)
async def async_write(
    db: sqlite3.Connection,
    user: Named[str],
    project: Named[str],
    password: str,
    *,
    admin: Proof[Admin],
    plan: Proof[Entitled],
) -> int:
    return await asyncio.to_thread(
        write, db, user, project, password, admin=admin, plan=plan
    )


@pytest.fixture
def db():
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.executescript(
        "CREATE TABLE project(id TEXT PRIMARY KEY, password TEXT);"
        "INSERT INTO project VALUES ('p1', 'old'), ('p2', 'old');"
    )
    yield connection
    connection.close()


def passwords(db):
    return db.execute("SELECT password FROM project ORDER BY id").fetchall()


def test_real_protected_write_and_async_boundary(db):
    with names("alice", "p1") as (user, project):
        admin = _admin.prove(user, project)
        plan = _plan.prove(project, evidence="pro")
        assert plan.evidence == "pro"
        assert write(db, user, project, "sync", admin=admin, plan=plan) == 1
        assert passwords(db) == [("sync",), ("old",)]
        assert (
            asyncio.run(async_write(db, user, project, "async", admin=admin, plan=plan))
            == 1
        )
        assert passwords(db) == [("async",), ("old",)]
        assert list(signature(write).parameters) == [
            "db",
            "user",
            "project",
            "password",
            "admin",
            "plan",
        ]


@pytest.mark.parametrize(
    "attack",
    [
        "missing",
        "dictionary",
        "none",
        "wrong_kind",
        "same_label",
        "wrong_user",
        "wrong_project",
        "same_value_new_name",
        "swapped",
        "wrong_arity",
        "raw_id",
        "missing_plan",
    ],
)
def test_invalid_proofs_fail_before_any_write(db, attack):
    with names("alice", "p1", "p2", "bob") as (user, project, other, other_user):
        proof = _admin.prove(user, project)
        plan = _plan.prove(project)
        args = [db, user, project, "unauthorized"]
        kwargs = {"admin": proof, "plan": plan}
        if attack == "missing":
            del kwargs["admin"]
        elif attack == "dictionary":
            kwargs["admin"] = {"kind": "Admin"}
        elif attack == "none":
            kwargs["admin"] = None
        elif attack == "wrong_kind":
            kwargs["admin"] = plan
        elif attack == "same_label":
            kwargs["admin"] = _impostor.prove(user, project)
        elif attack == "wrong_user":
            args[1] = other_user
        elif attack == "wrong_project":
            args[2] = other
        elif attack == "same_value_new_name":
            args[2] = name("p1")
        elif attack == "swapped":
            kwargs["admin"] = _admin.prove(project, user)
        elif attack == "wrong_arity":
            kwargs["admin"] = _admin.prove(project)
        elif attack == "raw_id":
            args[2] = "p1"
        elif attack == "missing_plan":
            del kwargs["plan"]
        with pytest.raises((AuthorizationError, TypeError)):
            write(*args, **kwargs)
        assert passwords(db) == [("old",), ("old",)]
        with pytest.raises((AuthorizationError, TypeError)):
            asyncio.run(async_write(*args, **kwargs))
        assert passwords(db) == [("old",), ("old",)]


def test_scope_exit_including_exception_and_cross_thread_close(db):
    with pytest.raises(ValueError):
        with names("alice", "p1") as (user, project):
            admin = _admin.prove(user, project)
            plan = _plan.prove(project)
            raise ValueError("consumer failed")
    with pytest.raises(AuthorizationError):
        write(db, user, project, "blocked", admin=admin, plan=plan)
    with pytest.raises(AuthorizationError):
        _admin.prove(user, project)
    with pytest.raises(AuthorizationError):
        _ = project.value
    assert passwords(db) == [("old",), ("old",)]
    scope = names("alice", "p1")
    user, project = scope.__enter__()
    admin = _admin.prove(user, project)
    plan = _plan.prove(project)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(scope.__exit__, None, None, None).result()
    with pytest.raises(AuthorizationError):
        write(db, user, project, "blocked", admin=admin, plan=plan)
    with pytest.raises(ValueError):
        scope.__enter__()
    assert passwords(db) == [("old",), ("old",)]


def test_opaque_handles_cannot_be_forged_modified_or_serialized():
    value = name("private-user-value")
    proof = _admin.prove(value)
    for cls in (Named, Names, Proof, ProofKind, Prover):
        with pytest.raises(TypeError):
            cls()
        with pytest.raises(TypeError):
            type("Forgery", (cls,), {})
    for item in (value, proof, _admin, _admin.kind, names("secret")):
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(item)
        with pytest.raises(AttributeError):
            item.forged = True
        assert "private-user-value" not in repr(item)
    with pytest.raises(AttributeError):
        value.value = "modified"
    with pytest.raises(AttributeError):
        proof.kind = "Plan"
    assert value.value == "private-user-value"


def test_limits_parameter_validation_and_safe_errors():
    for label in ("", "private-value!", "9invalid", "α", "a" * 129):
        with pytest.raises(ValueError) as failure:
            define_proof(label)
        assert "private-value" not in str(failure.value)
    assert _admin.kind.kind == "Admin"
    proof = _admin.prove()
    _admin.kind.require(proof)
    values = [name(i) for i in range(65)]
    _admin.prove(*values[:64])
    with pytest.raises(AuthorizationError):
        _admin.prove(*values)
    with pytest.raises(ValueError):
        names(*range(65))
    with pytest.raises(ValueError):
        requires()
    with pytest.raises(ValueError):
        requires(proof=Requirement(_admin.kind, ("missing",)))(lambda proof: None)
    with pytest.raises(ValueError):
        requires(args=Requirement(_admin.kind, ()))(lambda *args: None)
    with pytest.raises(TypeError):
        requires(proof="not a requirement")(lambda proof: None)
    assert Named[str] is not None
    assert Proof[Admin] is not None
