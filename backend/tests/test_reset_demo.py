"""The demo reset: restores the committed demo copy, with no AI calls."""

import sqlite3

import db
import reset_demo


def test_reset_restores_the_demo_and_keeps_the_old_database(tmp_path, monkeypatch, fake_llm):
    target = tmp_path / "ats.db"
    monkeypatch.setattr(db, "DB_PATH", target)
    db.init_db()
    with sqlite3.connect(target) as conn:  # something to lose: a role nobody else has
        conn.execute("INSERT INTO roles (title, requirements, description) VALUES ('Mine', '[]', 'jd')")

    kept = reset_demo.reset(target)

    assert fake_llm.calls == 0
    assert kept == tmp_path / "ats.before-reset.db"
    with sqlite3.connect(kept) as old:
        assert old.execute("SELECT title FROM roles").fetchall() == [("Mine",)]
    assert db.list_decisions(2) == []
    full_stack = db.list_candidates(2)
    stages = {c.cv_filename: c.stage for c in full_stack}
    assert sum(stage == "new" for stage in stages.values()) == 7
    assert stages["fse_layla_haddad_strong.txt"] == "shortlisted"
    assert stages["fse_omar_farouk_functional.txt"] == "interview"
    assert all(c.evidence_status == "complete" for c in full_stack)
    buried = {c.name for c in full_stack if any(r.buried for r in c.evidence.requirements)}
    assert buried == {"Daniel Mensah", "Rania Aziz"}  # the demo's two "Before you reject" candidates
