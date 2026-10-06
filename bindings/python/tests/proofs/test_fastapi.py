import sqlite3
from collections.abc import AsyncIterator
from typing import Annotated

import pytest
from fastapi import Body, Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from gdp import (
    AuthorizationError,
    Named,
    Proof,
    Requirement,
    define_proof,
    name,
    names,
    requires,
)


class Admin:
    pass


_admin = define_proof("ProjectAdmin", tag=Admin)
_other_admin = define_proof("ProjectAdmin", tag=Admin)


@requires(admin=Requirement(_admin.kind, ("user", "project")))
async def change_password(
    db: sqlite3.Connection,
    user: Named[str],
    project: Named[str],
    password: str,
    *,
    admin: Proof[Admin],
) -> None:
    db.execute("UPDATE projects SET password=? WHERE id=?", (password, project.value))
    db.commit()


def test_fastapi_request_scopes_and_rejected_proofs_prevent_database_writes(tmp_path):
    db = sqlite3.connect(tmp_path / "projects.db", check_same_thread=False)
    try:
        db.executescript(
            "CREATE TABLE projects(id TEXT PRIMARY KEY, password TEXT);"
            "CREATE TABLE admins(user TEXT, project TEXT);"
            "INSERT INTO projects VALUES ('p1', 'old'), ('p2', 'other');"
            "INSERT INTO admins VALUES ('alice', 'p1');"
        )
        admitted = []
        mode = "valid"
        app = FastAPI()

        async def subjects(
            project: str, user: Annotated[str, Header()]
        ) -> AsyncIterator[tuple[Named[str], Named[str]]]:
            with names(user, project) as pair:
                yield pair

        async def checked_admin(
            pair: Annotated[tuple[Named[str], Named[str]], Depends(subjects)],
        ) -> Proof[Admin]:
            user, project = pair
            if not db.execute(
                "SELECT 1 FROM admins WHERE user=? AND project=?",
                (user.value, project.value),
            ).fetchone():
                raise HTTPException(403, "Project administrator access is required")
            if mode == "wrong_subject":
                proof = _admin.prove(user, name("p2"))
            elif mode == "wrong_issuer":
                proof = _other_admin.prove(user, project)
            elif mode == "closed_scope":
                with names(user.value, project.value) as (
                    expired_user,
                    expired_project,
                ):
                    proof = _admin.prove(expired_user, expired_project)
            else:
                proof = _admin.prove(user, project)
            admitted.append((user, project, proof))
            return proof

        @app.put("/projects/{project}/password")
        async def update(
            password: Annotated[str, Body(embed=True)],
            pair: Annotated[tuple[Named[str], Named[str]], Depends(subjects)],
            admin: Annotated[Proof[Admin], Depends(checked_admin)],
        ) -> dict[str, str]:
            user, project = pair
            try:
                await change_password(db, user, project, password, admin=admin)
            except AuthorizationError as error:
                raise HTTPException(403, "Authorization proof was rejected") from error
            return {"status": "updated"}

        with TestClient(app) as client:
            assert app.openapi()["paths"]["/projects/{project}/password"]["put"]
            response = client.put(
                "/projects/p1/password",
                headers={"user": "alice"},
                json={"password": "first"},
            )
            assert response.status_code == 200, response.text
            user, project, proof = admitted[-1]
            with pytest.raises(AuthorizationError):
                _admin.kind.require(proof, user, project)
            for attack, actor in (
                ("valid", "bob"),
                ("wrong_subject", "alice"),
                ("wrong_issuer", "alice"),
                ("closed_scope", "alice"),
            ):
                mode = attack
                response = client.put(
                    "/projects/p1/password",
                    headers={"user": actor},
                    json={"password": "unauthorized"},
                )
                assert response.status_code == 403, response.text
                assert response.json()["detail"] in (
                    "Project administrator access is required",
                    "Authorization proof was rejected",
                )
                assert db.execute(
                    "SELECT password FROM projects ORDER BY id"
                ).fetchall() == [("first",), ("other",)]
            mode = "valid"
            response = client.put(
                "/projects/p1/password",
                headers={"user": "alice"},
                json={"password": "last"},
            )
            assert response.status_code == 200, response.text
            assert db.execute(
                "SELECT password FROM projects ORDER BY id"
            ).fetchall() == [("last",), ("other",)]
            user, project, proof = admitted[-1]
            with pytest.raises(AuthorizationError):
                _admin.kind.require(proof, user, project)
    finally:
        db.close()
