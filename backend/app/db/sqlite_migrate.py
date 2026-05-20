"""إصلاحات مخطط SQLite خفيفة (بدون Alembic) عند إضافة أعمدة جديدة."""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def apply_sqlite_schema_fixes(conn: Connection) -> None:
    users_tbl = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    ).scalar()
    if users_tbl:
        ucols = {r[1] for r in conn.execute(text("PRAGMA table_info(users)")).fetchall()}
        if "must_change_password" not in ucols:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0 NOT NULL")
            )
            conn.execute(
                text("UPDATE users SET must_change_password = 0 WHERE must_change_password IS NULL")
            )
        if "is_group_leader" not in ucols:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN is_group_leader BOOLEAN DEFAULT 0 NOT NULL")
            )
            conn.execute(
                text(
                    "UPDATE users SET is_group_leader = 1 WHERE id IN "
                    "(SELECT created_by FROM groups WHERE created_by IS NOT NULL)"
                )
            )

    sub_tbl = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='submissions'")
    ).scalar()

    if sub_tbl:
        cols = {r[1] for r in conn.execute(text("PRAGMA table_info(submissions)")).fetchall()}
        stmts: list[str] = []
        if "review_status" not in cols:
            stmts.append(
                "ALTER TABLE submissions ADD COLUMN review_status VARCHAR(30) DEFAULT 'pending'"
            )
        if "supervisor_grade" not in cols:
            stmts.append(
                "ALTER TABLE submissions ADD COLUMN supervisor_grade NUMERIC(5, 2)"
            )
        if "supervisor_feedback" not in cols:
            stmts.append("ALTER TABLE submissions ADD COLUMN supervisor_feedback TEXT")
        if "graded_by_id" not in cols:
            stmts.append("ALTER TABLE submissions ADD COLUMN graded_by_id INTEGER")
        if "graded_at" not in cols:
            stmts.append("ALTER TABLE submissions ADD COLUMN graded_at DATETIME")
        for stmt in stmts:
            conn.execute(text(stmt))
        conn.execute(
            text("UPDATE submissions SET review_status = 'pending' WHERE review_status IS NULL")
        )

    proj_tbl = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
    ).scalar()
    if proj_tbl:
        pcols = {r[1] for r in conn.execute(text("PRAGMA table_info(projects)")).fetchall()}
        if "grading_report_weight" not in pcols:
            conn.execute(
                text(
                    "ALTER TABLE projects ADD COLUMN grading_report_weight NUMERIC(5,2) DEFAULT 60"
                )
            )
        if "grading_individual_weight" not in pcols:
            conn.execute(
                text(
                    "ALTER TABLE projects ADD COLUMN grading_individual_weight NUMERIC(5,2) DEFAULT 40"
                )
            )
        conn.execute(
            text(
                "UPDATE projects SET grading_report_weight = 60 WHERE grading_report_weight IS NULL"
            )
        )
        conn.execute(
            text(
                "UPDATE projects SET grading_individual_weight = 40 WHERE grading_individual_weight IS NULL"
            )
        )
