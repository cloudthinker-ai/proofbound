from __future__ import annotations

from sqlite3 import Connection

from gdp import Named, Proof, Requirement, requires
from proofs.admin import Admin, ProjectAdmin
from proofs.plan import Entitled, PasswordProtectionPlan


@requires(
    admin=Requirement(ProjectAdmin, ("user", "project")),
    plan=Requirement(PasswordProtectionPlan, ("project",)),
)
def change_password(
    db: Connection,
    user: Named[str],
    project: Named[str],
    password: str,
    *,
    admin: Proof[Admin],
    plan: Proof[Entitled],
) -> None:
    db.execute(
        "UPDATE project SET password = ? WHERE id = ?", (password, project.value)
    )
    db.commit()
