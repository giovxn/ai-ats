"""API tests for Block 4: the evidence check at upload (and its retry), and the decision log."""

import sqlite3

import db
import llm
from schemas import EvidenceExtraction, EvidenceQuote, RequirementEvidence
from tests.test_candidates_api import make_role, upload


def new_candidate(client):
    return upload(client, make_role(client)["id"]).json()


# ---------- evidence ----------

def test_upload_checks_evidence(client, fake_llm):
    fake_llm.evidence_result = EvidenceExtraction(
        requirements=[RequirementEvidence(requirement_number=1, status="demonstrated", quotes=[
            # No job: the fake CV text doesn't contain the fake profile's second job (EY), so job
            # sections can't be found; a quote checked against the text alone still verifies.
            EvidenceQuote(text="Led IFRS consolidation for nine entities", job_number=None, tags=[]),
        ])],
        recent_highlights=[],
    )

    candidate = new_candidate(client)

    assert fake_llm.calls == 3  # role, CV, evidence
    assert candidate["evidence_status"] == "complete"
    acca, netsuite = candidate["evidence"]["requirements"]
    assert (acca["text"], acca["must_have"], acca["status"]) == ("ACCA, CPA or CA", True, "demonstrated")
    assert acca["quotes"][0]["text"] == "Led IFRS consolidation for nine entities"
    assert netsuite["status"] == "not_found"  # the AI didn't mention it
    assert client.get(f"/api/candidates/{candidate['id']}").json() == candidate


def test_failed_evidence_check_still_saves_the_candidate_and_can_be_retried(client, fake_llm):
    fake_llm.evidence_error = llm.LLMError("The AI took too long to answer. Try again.")

    response = upload(client, make_role(client)["id"])

    assert response.status_code == 201
    candidate = response.json()
    assert candidate["name"] == "Fatima Khoury"
    assert (candidate["evidence_status"], candidate["evidence"]) == ("failed", None)

    # Retry while the AI still fails: a readable error, still "failed".
    retry = client.post(f"/api/candidates/{candidate['id']}/evidence")
    assert retry.status_code == 502
    assert retry.json()["detail"] == "The AI took too long to answer. Try again."

    fake_llm.evidence_error = None
    retry = client.post(f"/api/candidates/{candidate['id']}/evidence")
    assert retry.status_code == 200
    assert retry.json()["evidence_status"] == "complete"
    assert db.candidates_without_evidence() == []


def test_retry_for_a_missing_candidate_is_404(client, fake_llm):
    assert client.post("/api/candidates/999/evidence").status_code == 404


def test_older_databases_get_the_evidence_columns_as_pending(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript("""
        CREATE TABLE roles (id INTEGER PRIMARY KEY, title TEXT NOT NULL, location TEXT,
            requirements TEXT NOT NULL, description TEXT NOT NULL, created_at TEXT);
        CREATE TABLE candidates (id INTEGER PRIMARY KEY, role_id INTEGER NOT NULL, stage TEXT NOT NULL,
            name TEXT, current_title TEXT, years_experience REAL, skills TEXT NOT NULL, jobs TEXT NOT NULL,
            education TEXT NOT NULL, summary TEXT NOT NULL, cv_filename TEXT NOT NULL, cv_text TEXT NOT NULL,
            cv_hash TEXT NOT NULL, created_at TEXT NOT NULL);
        INSERT INTO roles VALUES (1, 'Engineer', NULL, '[]', 'jd', '2026-11-01');
        INSERT INTO candidates VALUES (1, 1, 'new', 'Sam', NULL, NULL, '[]', '[]', '[]', 's', 'a.txt', 'cv', 'h', '2026-11-01');
    """)
    old.close()
    monkeypatch.setattr(db, "DB_PATH", path)

    db.init_db()

    candidate = db.get_candidate(1)
    assert (candidate.evidence_status, candidate.evidence) == ("pending", None)
    assert [c.id for c in db.candidates_without_evidence()] == [1]


# ---------- decision log ----------

def decide(client, candidate_id, **body):
    return client.post(f"/api/candidates/{candidate_id}/decisions", json=body)


def test_decision_moves_the_candidate_and_logs_it(client, fake_llm):
    candidate = new_candidate(client)

    response = decide(client, candidate["id"], to_stage="rejected", prompt_shown=True, prompt_choice="reject_anyway")

    assert response.status_code == 201
    result = response.json()
    assert result["candidate"]["stage"] == "rejected"
    decision = result["decision"]
    assert (decision["from_stage"], decision["to_stage"]) == ("new", "rejected")
    assert (decision["prompt_shown"], decision["prompt_choice"], decision["undo_of"]) == (True, "reject_anyway", None)


def test_undo_after_reject_adds_an_entry_and_keeps_the_original(client, fake_llm):
    candidate = new_candidate(client)
    reject = decide(client, candidate["id"], to_stage="rejected").json()["decision"]

    undo = decide(client, candidate["id"], to_stage="new", undo_of=reject["id"])

    assert undo.status_code == 201
    assert undo.json()["candidate"]["stage"] == "new"
    log = client.get(f"/api/roles/{candidate['role_id']}/decisions").json()
    assert [(d["from_stage"], d["to_stage"], d["undo_of"]) for d in log] == [
        ("new", "rejected", None),
        ("rejected", "new", reject["id"]),
    ]


def test_look_again_logs_without_moving(client, fake_llm):
    candidate = new_candidate(client)

    response = decide(client, candidate["id"], to_stage="new", prompt_shown=True, prompt_choice="look_again")

    assert response.status_code == 201
    assert response.json()["candidate"]["stage"] == "new"
    assert response.json()["decision"]["prompt_choice"] == "look_again"


def test_inconsistent_decisions_are_rejected(client, fake_llm):
    candidate = new_candidate(client)
    other = upload(client, candidate["role_id"], text="Someone else entirely. " * 10, filename="b.txt").json()
    other_decision = decide(client, other["id"], to_stage="interview").json()["decision"]

    cases = [
        dict(to_stage="rejected", prompt_shown=True, prompt_choice="look_again"),  # look again doesn't move
        dict(to_stage="shortlisted", prompt_shown=True, prompt_choice="reject_anyway"),
        dict(to_stage="rejected", prompt_choice="reject_anyway"),  # a choice without a prompt
        dict(to_stage="new", undo_of=other_decision["id"]),  # someone else's decision
        dict(to_stage="archived"),
    ]
    for body in cases:
        assert decide(client, candidate["id"], **body).status_code == 422, body
    assert client.get(f"/api/candidates/{candidate['id']}").json()["stage"] == "new"
    assert len(client.get(f"/api/roles/{candidate['role_id']}/decisions").json()) == 1  # only the other one


def test_decisions_for_missing_things_are_404(client, fake_llm):
    assert decide(client, 999, to_stage="rejected").status_code == 404
    assert client.get("/api/roles/999/decisions").status_code == 404
