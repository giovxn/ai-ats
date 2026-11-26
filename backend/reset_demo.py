"""Put the demo back, in one command and with no AI calls.

Restores demo.db into ats.db: the 4 sample roles and 18 fictional sample CVs, evidence already
checked, every candidate in its demo stage (7 in New on the Full-Stack role), and an empty
decision log. Your current ats.db is kept as ats.before-reset.db first (replaced on each reset).

    cd backend && uv run python reset_demo.py

Safe while the backend runs: SQLite's backup API copies the database properly, so the server
just sees the new data on its next request.

demo.db was made by uploading sample_data/cvs to the sample roles, running backfill_evidence.py,
setting the demo stages and clearing the decision log.
"""

import sqlite3
from pathlib import Path

import db

DEMO_PATH = Path(__file__).parent / "demo.db"


def _copy(source: Path, target: Path) -> None:
    src, dst = sqlite3.connect(source), sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()


def reset(target: Path | None = None) -> Path | None:
    """Restore the demo into target (ats.db by default). Returns where the old database was kept."""
    target = target or db.DB_PATH
    kept = None
    if target.exists():
        kept = target.with_name("ats.before-reset.db")
        _copy(target, kept)
    _copy(DEMO_PATH, target)
    return kept


if __name__ == "__main__":
    kept = reset()
    db.init_db()  # in case demo.db is older than the current schema
    print("Demo restored: every candidate in its demo stage, decision log empty.")
    if kept:
        print(f"Your previous database is in {kept.name}.")
