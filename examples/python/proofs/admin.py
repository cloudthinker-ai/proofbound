from __future__ import annotations

from sqlite3 import Connection

from gdp import Named, Proof, define_proof


class Admin:
    pass


_issuer = define_proof("ProjectAdmin", tag=Admin)
ProjectAdmin = _issuer.kind


def check_admin(
    db: Connection, user: Named[str], project: Named[str]
) -> Proof[Admin] | None:
    row = db.execute(
        "SELECT role FROM membership WHERE user_id = ? AND project_id = ?",
        (user.value, project.value),
    ).fetchone()
    if row is None or row[0] not in ("owner", "admin"):
        return None
    return _issuer.prove(user, project)
