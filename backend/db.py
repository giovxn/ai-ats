"""SQLite storage, using Python's built-in sqlite3 module.

Lists (requirements, skills, jobs, education) are stored as JSON text in a single column. That keeps the
schema to one table per concept, which is enough for a single-user demo.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from schemas import Candidate, CVProfile, Role, RoleExtraction, Stage

DB_PATH = Path(__file__).parent / "ats.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS roles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    location     TEXT,
    requirements TEXT NOT NULL,  -- JSON: [{"text": ..., "must_have": ...}]
    excluded_criteria TEXT NOT NULL DEFAULT '[]',  -- JSON: discriminatory criteria found in the ad, not used
    description  TEXT NOT NULL,  -- the original pasted job description
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A candidate is one CV uploaded to one role (person and application merged; see NOTES.md).
CREATE TABLE IF NOT EXISTS candidates (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id          INTEGER NOT NULL REFERENCES roles(id),
    stage            TEXT NOT NULL DEFAULT 'new'
                     CHECK (stage IN ('new', 'shortlisted', 'interview', 'rejected')),
    name             TEXT,
    current_title    TEXT,
    years_experience REAL,
    skills           TEXT NOT NULL,  -- JSON: ["IFRS", "React", ...]
    jobs             TEXT NOT NULL,  -- JSON: [{"title", "company", "start", "end", "is_current", "highlights"}]
    education        TEXT NOT NULL,  -- JSON: [{"qualification", "institution", "year"}]
    summary          TEXT NOT NULL,
    cv_filename      TEXT NOT NULL,
    cv_text          TEXT NOT NULL,  -- the text extracted from the file
    cv_hash          TEXT NOT NULL,  -- fingerprint of cv_text, to spot the same CV uploaded twice
    created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (role_id, cv_hash)
);
"""


class DuplicateCV(Exception):
    """The same CV is already on this role."""


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
        # Databases created before excluded_criteria existed get the column added.
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(roles)")]
        if "excluded_criteria" not in columns:
            conn.execute("ALTER TABLE roles ADD COLUMN excluded_criteria TEXT NOT NULL DEFAULT '[]'")


# ---------- roles ----------

def _row_to_role(row: sqlite3.Row) -> Role:
    return Role(**{
        **dict(row),
        "requirements": json.loads(row["requirements"]),
        "excluded_criteria": json.loads(row["excluded_criteria"]),
    })


def create_role(description: str, extracted: RoleExtraction) -> Role:
    requirements = json.dumps([r.model_dump() for r in extracted.requirements])
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO roles (title, location, requirements, excluded_criteria, description)"
            " VALUES (?, ?, ?, ?, ?)",
            (extracted.title, extracted.location, requirements,
             json.dumps(extracted.excluded_criteria), description),
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


# ---------- candidates ----------

def _row_to_candidate(row: sqlite3.Row) -> Candidate:
    data = dict(row)
    for column in ("skills", "jobs", "education"):
        data[column] = json.loads(data[column])
    return Candidate(**data)


def candidate_exists(role_id: int, cv_hash: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM candidates WHERE role_id = ? AND cv_hash = ?", (role_id, cv_hash)
        ).fetchone()
    return row is not None


def create_candidate(
    role_id: int,
    profile: CVProfile,
    years_experience: float | None,
    cv_filename: str,
    cv_text: str,
    cv_hash: str,
) -> Candidate:
    try:
        with get_db() as conn:
            cursor = conn.execute(
                """INSERT INTO candidates (role_id, name, current_title, years_experience, skills, jobs,
                                          education, summary, cv_filename, cv_text, cv_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    role_id,
                    profile.name,
                    profile.current_title,
                    years_experience,
                    json.dumps(profile.skills),
                    json.dumps([job.model_dump() for job in profile.jobs]),
                    json.dumps([item.model_dump() for item in profile.education]),
                    profile.summary,
                    cv_filename,
                    cv_text,
                    cv_hash,
                ),
            )
            row = conn.execute("SELECT * FROM candidates WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError as error:
        # Two uploads of the same CV at once both pass candidate_exists; the UNIQUE rule catches the second.
        raise DuplicateCV() from error
    return _row_to_candidate(row)


def list_candidates(role_id: int) -> list[Candidate]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM candidates WHERE role_id = ? ORDER BY id DESC", (role_id,)
        ).fetchall()
    return [_row_to_candidate(row) for row in rows]


def get_candidate(candidate_id: int) -> Candidate | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    return _row_to_candidate(row) if row else None


def update_stage(candidate_id: int, stage: Stage) -> Candidate | None:
    """Move a candidate to another stage. Returns None if there is no such candidate."""
    with get_db() as conn:
        conn.execute("UPDATE candidates SET stage = ? WHERE id = ?", (stage, candidate_id))
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    return _row_to_candidate(row) if row else None
