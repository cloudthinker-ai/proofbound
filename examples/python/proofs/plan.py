from __future__ import annotations

from sqlite3 import Connection

from gdp import Named, Proof, define_proof


class Entitled:
    pass


_issuer = define_proof("PasswordProtectionPlan", tag=Entitled)
PasswordProtectionPlan = _issuer.kind


def check_plan(db: Connection, project: Named[str]) -> Proof[Entitled] | None:
    row = db.execute(
        "SELECT plan FROM project WHERE id = ?", (project.value,)
    ).fetchone()
    if row is None or row[0] != "pro":
        return None
    return _issuer.prove(project, evidence=row[0])
