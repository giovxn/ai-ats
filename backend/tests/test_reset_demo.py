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
    assert [r.title for r in db.list_roles()] == ["Full-Stack Software Engineer"]  # 1 job ad, as the brief asks
    assert db.list_roles()[0].excluded_criteria == ["Preferred age 25 to 35"]
    assert db.list_decisions(1) == []
    candidates = db.list_candidates(1)
    assert len(candidates) == 9
    assert all(c.stage == "new" and c.evidence_status == "complete" for c in candidates)
    buried = {c.name for c in candidates if any(r.buried for r in c.evidence.requirements)}
    assert buried == {"Priya Raman", "Rafael Costa"}  # the demo's two "Before you reject" candidates
