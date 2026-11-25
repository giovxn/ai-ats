"""API tests for Block 3 (pipeline): moving candidates between stages."""

from tests.test_candidates_api import make_role, upload


def new_candidate(client):
    return upload(client, make_role(client)["id"]).json()


def test_move_candidate_saves_the_new_stage(client, fake_llm):
    candidate = new_candidate(client)

    response = client.patch(f"/api/candidates/{candidate['id']}", json={"stage": "shortlisted"})

    assert response.status_code == 200
    moved = response.json()
    assert moved["stage"] == "shortlisted"
    assert {**moved, "stage": "new"} == candidate  # nothing else changed
    assert client.get(f"/api/candidates/{candidate['id']}").json()["stage"] == "shortlisted"
    assert client.get(f"/api/roles/{candidate['role_id']}/candidates").json()[0]["stage"] == "shortlisted"


def test_full_mini_hiring_process(client, fake_llm):
    candidate = new_candidate(client)
    for stage in ["shortlisted", "interview", "rejected", "interview"]:  # moving back is allowed
        assert client.patch(f"/api/candidates/{candidate['id']}", json={"stage": stage}).status_code == 200
    assert client.get(f"/api/candidates/{candidate['id']}").json()["stage"] == "interview"


def test_moving_to_the_same_stage_is_allowed(client, fake_llm):
    candidate = new_candidate(client)

    response = client.patch(f"/api/candidates/{candidate['id']}", json={"stage": "new"})

    assert response.status_code == 200
    assert response.json()["stage"] == "new"


def test_unknown_stage_is_rejected_and_nothing_changes(client, fake_llm):
    candidate = new_candidate(client)

    for body in [{"stage": "hired"}, {"stage": "Shortlisted"}, {"stage": ""}, {}]:
        assert client.patch(f"/api/candidates/{candidate['id']}", json=body).status_code == 422
    assert client.get(f"/api/candidates/{candidate['id']}").json()["stage"] == "new"


def test_unknown_candidate_returns_404(client):
    response = client.patch("/api/candidates/9999", json={"stage": "shortlisted"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate not found."
