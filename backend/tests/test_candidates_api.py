"""API tests for Block 2 (candidates): real routes and a real (temporary) database, fake LLM."""

import pytest

import db
import llm

CV = ("Fatima Khoury\nFinancial Controller, Gulfway Freight, May 2021 - present\n"
      + "Led IFRS consolidation for nine entities and the NetSuite migration. " * 3)


def make_role(client):
    return client.post("/api/roles", json={"description": "Senior Accountant in Abu Dhabi. " * 3}).json()


def upload(client, role_id, text=CV, filename="fatima.txt"):
    return client.post(f"/api/roles/{role_id}/candidates", files={"file": (filename, text.encode(), "text/plain")})


def test_upload_saves_and_returns_the_profile(client, fake_llm):
    role = make_role(client)

    response = upload(client, role["id"])

    assert response.status_code == 201
    candidate = response.json()
    assert candidate["role_id"] == role["id"]
    assert candidate["stage"] == "new"
    assert candidate["name"] == "Fatima Khoury"
    assert candidate["skills"] == ["IFRS", "ACCA", "NetSuite"]
    assert [j["company"] for j in candidate["jobs"]] == ["Gulfway Freight", "EY"]
    assert candidate["education"][0]["qualification"] == "BBA Accounting"
    assert candidate["cv_filename"] == "fatima.txt"
    assert candidate["cv_text"] == CV.strip()
    assert candidate["years_experience"] > 9  # counted from the job dates, not by the LLM
    assert "cv_hash" not in candidate  # internal only
    # Persisted: readable by id and in the role's list.
    assert client.get(f"/api/candidates/{candidate['id']}").json() == candidate
    assert client.get(f"/api/roles/{role['id']}/candidates").json() == [candidate]


def test_same_cv_twice_is_rejected_without_calling_the_llm_again(client, fake_llm):
    role = make_role(client)
    upload(client, role["id"])
    calls_after_first = fake_llm.calls

    response = upload(client, role["id"], text=CV.upper(), filename="copy.txt")

    assert response.status_code == 409
    assert "already uploaded" in response.json()["detail"]
    assert fake_llm.calls == calls_after_first
    assert len(client.get(f"/api/roles/{role['id']}/candidates").json()) == 1


def test_same_cv_can_go_to_two_different_roles(client, fake_llm):
    first, second = make_role(client), make_role(client)

    assert upload(client, first["id"]).status_code == 201
    assert upload(client, second["id"]).status_code == 201


def test_text_that_is_not_a_cv_is_rejected_and_not_saved(client, fake_llm):
    role = make_role(client)
    fake_llm.cv_result = fake_llm.cv_result.model_copy(update={"is_cv": False})

    response = upload(client, role["id"])

    assert response.status_code == 422
    assert "doesn't look like a CV" in response.json()["detail"]
    assert client.get(f"/api/roles/{role['id']}/candidates").json() == []


def test_unusable_file_is_rejected_before_the_llm(client, fake_llm):
    role = make_role(client)
    calls_before = fake_llm.calls

    response = upload(client, role["id"], filename="cv.docx")

    assert response.status_code == 415
    assert response.json()["detail"] == "Upload a PDF or .txt file."
    assert fake_llm.calls == calls_before


def test_llm_failure_returns_502_and_saves_nothing(client, fake_llm):
    role = make_role(client)
    fake_llm.error = llm.LLMError("The AI took too long to answer. Try again.")

    response = upload(client, role["id"])

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI took too long to answer. Try again."
    assert client.get(f"/api/roles/{role['id']}/candidates").json() == []


def test_unknown_role_returns_404(client, fake_llm):
    assert upload(client, 9999).status_code == 404
    assert client.get("/api/roles/9999/candidates").status_code == 404
    assert fake_llm.calls == 0


def test_unknown_candidate_returns_404(client):
    assert client.get("/api/candidates/9999").status_code == 404


def test_upload_without_a_file_returns_422(client, fake_llm):
    role = make_role(client)
    assert client.post(f"/api/roles/{role['id']}/candidates").status_code == 422



def test_database_rejects_a_duplicate_that_slips_past_the_check(client, fake_llm):
    # Two uploads of the same CV at the same moment both pass candidate_exists();
    # the UNIQUE (role_id, cv_hash) rule must still stop the second one.
    role = make_role(client)
    db.create_candidate(role["id"], fake_llm.cv_result, 1.0, "a.txt", CV, "same-hash")

    with pytest.raises(db.DuplicateCV):
        db.create_candidate(role["id"], fake_llm.cv_result, 1.0, "b.txt", CV, "same-hash")
