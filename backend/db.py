"""SQLite storage, using Python's built-in sqlite3 module.

Lists (requirements) are stored as JSON text in a single column. That keeps the
schema to one table per concept, which is enough for a single-user demo.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from schemas import Role, RoleExtraction

DB_PATH = Path(__file__).parent / "ats.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS roles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    location     TEXT,
    requirements TEXT NOT NULL,  -- JSON: [{"text": ..., "must_have": ...}]
    description  TEXT NOT NULL,  -- the original pasted job description
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


@contextmanager
def get_db():
    """Open a connection, commit if everything worked, always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(SCHEMA)


# ---------- roles ----------

def _row_to_role(row: sqlite3.Row) -> Role:
    return Role(**{**dict(row), "requirements": json.loads(row["requirements"])})


def create_role(description: str, extracted: RoleExtraction) -> Role:
    requirements = json.dumps([r.model_dump() for r in extracted.requirements])
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO roles (title, location, requirements, description) VALUES (?, ?, ?, ?)",
            (extracted.title, extracted.location, requirements, description),
        )
        row = conn.execute("SELECT * FROM roles WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_role(row)


def list_roles() -> list[Role]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM roles ORDER BY id DESC").fetchall()
    return [_row_to_role(row) for row in rows]


def get_role(role_id: int) -> Role | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
    return _row_to_role(row) if row else None
