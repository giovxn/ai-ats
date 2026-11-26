"""SQLite storage, using Python's built-in sqlite3 module.

Lists (requirements, skills, jobs, education) are stored as JSON text in a single column. That keeps the
schema to one table per concept, which is enough for a single-user demo.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import cvs
import evidence
from schemas import Candidate, CVProfile, Decision, DecisionCreate, EvidenceState, Job, Role, RoleExtraction, Stage

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
    evidence_status  TEXT NOT NULL DEFAULT 'pending'
                     CHECK (evidence_status IN ('pending', 'complete', 'failed')),
    evidence         TEXT,           -- JSON from evidence.from_extraction; NULL until complete
    UNIQUE (role_id, cv_hash)
);

-- Block 4: every Scan mode decision. Rows are only added: an undo is a new row pointing at the old one.
CREATE TABLE IF NOT EXISTS decisions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id  INTEGER NOT NULL REFERENCES candidates(id),
    from_stage    TEXT NOT NULL,
    to_stage      TEXT NOT NULL,
    prompt_shown  INTEGER NOT NULL,  -- 0/1: the "Before you reject" check appeared
    prompt_choice TEXT CHECK (prompt_choice IN ('look_again', 'reject_anyway')),
    undo_of       INTEGER REFERENCES decisions(id),
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
        # Block 4 columns, added to databases from Blocks 2 and 3. Existing candidates start as
        # pending; backfill_evidence.py checks them.
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(candidates)")]
        if "evidence_status" not in columns:
            conn.execute(
                "ALTER TABLE candidates ADD COLUMN evidence_status TEXT NOT NULL DEFAULT 'pending'"
                " CHECK (evidence_status IN ('pending', 'complete', 'failed'))"
            )
        if "evidence" not in columns:
            conn.execute("ALTER TABLE candidates ADD COLUMN evidence TEXT")


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
    # Worked out from the CV text on every read, so older candidates get them too.
    data["email"] = cvs.find_email(data["cv_text"])
    data["phone"] = cvs.find_phone(data["cv_text"])
    data["links"] = cvs.find_links(data["cv_text"])
    # Quotes are verified and the buried rule applied on every read (plain code, no AI call).
    stored = json.loads(data["evidence"]) if data["evidence"] else None
    data["evidence"] = (
        evidence.view(stored, data["cv_text"], [Job(**job) for job in data["jobs"]])
        if stored and data["evidence_status"] == "complete" else None
    )
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


def save_evidence(candidate_id: int, status: EvidenceState, stored: dict | None) -> Candidate | None:
    """Record the result of an evidence check. Only a complete check replaces the stored evidence."""
    with get_db() as conn:
        if stored is None:
            conn.execute("UPDATE candidates SET evidence_status = ? WHERE id = ?", (status, candidate_id))
        else:
            conn.execute(
                "UPDATE candidates SET evidence_status = ?, evidence = ? WHERE id = ?",
                (status, json.dumps(stored), candidate_id),
            )
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    return _row_to_candidate(row) if row else None


def candidates_without_evidence() -> list[Candidate]:
    """Pending or failed: what backfill_evidence.py works through."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM candidates WHERE evidence_status != 'complete' ORDER BY id"
        ).fetchall()
    return [_row_to_candidate(row) for row in rows]


# ---------- Block 4: decision log ----------

class InvalidDecision(Exception):
    """The decision doesn't fit the candidate's current state. The message is shown to the user."""


def _row_to_decision(row: sqlite3.Row) -> Decision:
    return Decision(**{**dict(row), "prompt_shown": bool(row["prompt_shown"])})


def record_decision(candidate_id: int, body: DecisionCreate) -> tuple[Candidate, Decision] | None:
    """Move the candidate and log it, in one transaction. None if there is no such candidate."""
    with get_db() as conn:
        row = conn.execute("SELECT stage FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if row is None:
            return None
        from_stage = row["stage"]
        if body.prompt_choice == "look_again" and body.to_stage != from_stage:
            raise InvalidDecision("Look again doesn't change the stage.")
        if body.prompt_choice == "reject_anyway" and body.to_stage != "rejected":
            raise InvalidDecision("Reject anyway must move the candidate to Rejected.")
        if body.undo_of is not None:
            undone = conn.execute(
                "SELECT 1 FROM decisions WHERE id = ? AND candidate_id = ?", (body.undo_of, candidate_id)
            ).fetchone()
            if undone is None:
                raise InvalidDecision("There's no such decision to undo for this candidate.")

        conn.execute("UPDATE candidates SET stage = ? WHERE id = ?", (body.to_stage, candidate_id))
        cursor = conn.execute(
            "INSERT INTO decisions (candidate_id, from_stage, to_stage, prompt_shown, prompt_choice, undo_of)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (candidate_id, from_stage, body.to_stage, int(body.prompt_shown), body.prompt_choice, body.undo_of),
        )
        decision = conn.execute("SELECT * FROM decisions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        candidate = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    return _row_to_candidate(candidate), _row_to_decision(decision)


def list_decisions(role_id: int) -> list[Decision]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT decisions.* FROM decisions JOIN candidates ON candidates.id = decisions.candidate_id
               WHERE candidates.role_id = ? ORDER BY decisions.id""",
            (role_id,),
        ).fetchall()
    return [_row_to_decision(row) for row in rows]
