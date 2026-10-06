from __future__ import annotations

import asyncio
import gc
import pickle
import sqlite3
import weakref
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


class CyclicValue:
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


def test_call_layouts_always_check_current_authority_and_release_request_values(db):
    with names("alice", "p1", "p2") as (user, project, other):
        admin = _admin.prove(user, project)
        plan = _plan.prove(project)

        @requires(
            admin=Requirement(_admin.kind, ("user", "project")),
            plan=Requirement(_plan.kind, ("project",)),
        )
        def flexible(
            connection=db,
            user=user,
            /,
            project=project,
            *extra,
            admin=admin,
            plan=plan,
            password="changed",
            **options,
        ):
            return connection.execute(
                "UPDATE project SET password=? WHERE id=?", (password, project.value)
            ).rowcount

        calls = [
            ((), {}),
            ((db, user), {"project": project, "admin": admin, "plan": plan}),
            ((db, user, project, "extra"), {"plan": plan, "admin": admin}),
            ((db, user), {"user": other, "project": project, "admin": admin}),
        ]
        for args, kwargs in calls:
            assert flexible(*args, **kwargs) == 1
        assert passwords(db) == [("changed",), ("old",)]
        for index in range(140):
            assert flexible(db, user, project, **{f"option_{index}": index}) == 1
        for proof in (None, {"kind": "Admin"}, _impostor.prove(user, project)):
            with pytest.raises(AuthorizationError):
                flexible(db, user, project, admin=proof, password="forbidden")
        with pytest.raises(AuthorizationError):
            flexible(db, user, other, admin=admin, password="forbidden")
        assert passwords(db) == [("changed",), ("old",)]
        with pytest.raises(TypeError):
            flexible(db, user, project, project=project)
        for args, kwargs in (
            ((db, user, project), {"admin": admin, "plan": plan}),
            ((db, user, project, "bad", "extra"), {"admin": admin, "plan": plan}),
            (
                (db, user, project, "bad"),
                {"password": "duplicate", "admin": admin, "plan": plan},
            ),
            (
                (db, user, project, "bad"),
                {"unexpected": "bad", "admin": admin, "plan": plan},
            ),
        ):
            with pytest.raises(TypeError) as expected:
                signature(write).bind(*args, **kwargs)
            with pytest.raises(TypeError) as failure:
                write(*args, **kwargs)
            assert str(failure.value) == str(expected.value)
        assert passwords(db) == [("changed",), ("old",)]
    with pytest.raises(AuthorizationError):
        flexible()
    assert passwords(db) == [("changed",), ("old",)]

    value = CyclicValue()
    reference = weakref.ref(value)
    with names(value, "p1") as (temporary_user, temporary_project):
        temporary_admin = _admin.prove(
            temporary_user, temporary_project, evidence=value
        )
        temporary_plan = _plan.prove(temporary_project)
        assert (
            write(
                db,
                temporary_user,
                temporary_project,
                "released",
                admin=temporary_admin,
                plan=temporary_plan,
            )
            == 1
        )
    del value, temporary_user, temporary_project, temporary_admin, temporary_plan
    gc.collect()
    assert reference() is None


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


@pytest.mark.parametrize("kind", ["named", "scoped_named", "evidence", "scope"])
def test_python_reference_cycles_are_collectible(kind):
    value = CyclicValue()
    reference = weakref.ref(value)
    if kind == "named":
        handle = name(value)
    elif kind == "scoped_named":
        with names(value) as (handle,):
            assert handle.value is value
    elif kind == "evidence":
        handle = _admin.prove(evidence=value)
        assert handle.evidence is value
    else:
        handle = names(value)
    value.handle = handle
    gc.collect()
    assert reference() is value
    if kind == "named":
        assert handle.value is value
    elif kind == "evidence":
        assert handle.evidence is value
    elif kind == "scoped_named":
        with pytest.raises(AuthorizationError):
            _ = handle.value
    else:
        with handle as (subject,):
            assert subject.value is value
        del subject
    del value, handle
    gc.collect()
    assert reference() is None


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
