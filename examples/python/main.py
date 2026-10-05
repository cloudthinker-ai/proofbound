import sqlite3

from gdp import AuthorizationError, names
from operations import change_password
from proofs.admin import check_admin
from proofs.plan import check_plan


def main() -> None:
    with sqlite3.connect(":memory:") as db:
        db.executescript(
            "CREATE TABLE membership(user_id TEXT, project_id TEXT, role TEXT);"
            "CREATE TABLE project(id TEXT PRIMARY KEY, plan TEXT, password TEXT);"
            "INSERT INTO membership VALUES ('alice', 'p1', 'admin');"
            "INSERT INTO project VALUES ('p1', 'pro', 'old'), ('p2', 'pro', 'old');"
        )
        with names("alice", "p1", "p2") as (user, project, other):
            admin = check_admin(db, user, project)
            plan = check_plan(db, project)
            if admin is None or plan is None:
                raise PermissionError("Project admin and eligible plan are required")
            change_password(db, user, project, "new", admin=admin, plan=plan)
            assert db.execute(
                "SELECT password FROM project WHERE id='p1'"
            ).fetchone() == ("new",)
            print("Authorized write: p1 password changed")
            try:
                change_password(db, user, other, "blocked", admin=admin, plan=plan)
            except AuthorizationError:
                assert db.execute(
                    "SELECT password FROM project WHERE id='p2'"
                ).fetchone() == ("old",)
                print("Wrong-project proof: rejected before write")
            else:
                raise AssertionError("Wrong-project proof was accepted")


if __name__ == "__main__":
    main()
