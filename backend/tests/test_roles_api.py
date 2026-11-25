"""API tests for Block 1 (roles): real routes and a real (temporary) database, fake LLM."""

import llm
from tests.conftest import JD


def test_create_role_saves_and_returns_it(client, fake_llm):
    response = client.post("/api/roles", json={"description": JD})

    assert response.status_code == 201
    role = response.json()
    assert role["title"] == "Senior Accountant"
    assert role["location"] == "Abu Dhabi, UAE"
    assert role["requirements"] == [
        {"text": "ACCA, CPA or CA", "must_have": True},
        {"text": "NetSuite experience", "must_have": False},
    ]
    assert role["excluded_criteria"] == []
    assert role["description"] == JD
    # Persisted: readable by id and in the list.
    assert client.get(f"/api/roles/{role['id']}").json() == role
    assert client.get("/api/roles").json() == [role]


def test_too_short_description_is_rejected_without_calling_llm(client, fake_llm):
    response = client.post("/api/roles", json={"description": "Accountant needed"})

    assert response.status_code == 422
    assert fake_llm.calls == 0


def test_whitespace_padding_does_not_count_towards_min_length(client, fake_llm):
    response = client.post("/api/roles", json={"description": "Accountant" + " " * 60})

    assert response.status_code == 422
    assert fake_llm.calls == 0


def test_too_long_description_is_rejected(client, fake_llm):
    response = client.post("/api/roles", json={"description": "a" * 20_001})

    assert response.status_code == 422
    assert fake_llm.calls == 0


def test_non_job_description_is_rejected_and_not_saved(client, fake_llm):
    fake_llm.result = fake_llm.result.model_copy(update={"title": ""})

    response = client.post("/api/roles", json={"description": JD})

    assert response.status_code == 422
    assert "doesn't look like a job description" in response.json()["detail"]
    assert client.get("/api/roles").json() == []


def test_llm_failure_returns_502_and_saves_nothing(client, fake_llm):
    fake_llm.error = llm.LLMError("The AI took too long to answer. Try again.")

    response = client.post("/api/roles", json={"description": JD})

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI took too long to answer. Try again."
    assert client.get("/api/roles").json() == []


def test_unknown_role_id_returns_404(client):
    response = client.get("/api/roles/9999")

    assert response.status_code == 404


def test_roles_are_listed_newest_first(client, fake_llm):
    first = client.post("/api/roles", json={"description": JD}).json()
    second = client.post("/api/roles", json={"description": JD}).json()

    ids = [role["id"] for role in client.get("/api/roles").json()]
    assert ids == [second["id"], first["id"]]


def test_discriminatory_criteria_are_saved_apart_from_requirements(client, fake_llm):
    fake_llm.result = fake_llm.result.model_copy(
        update={"excluded_criteria": ["Male candidates only", " Age 25 to 35 ", ".", ""]}
    )

    role = client.post("/api/roles", json={"description": JD}).json()

    assert role["excluded_criteria"] == ["Male candidates only", "Age 25 to 35"]
    assert all("Male" not in r["text"] for r in role["requirements"])
    assert client.get(f"/api/roles/{role['id']}").json()["excluded_criteria"] == role["excluded_criteria"]


def test_old_database_gets_the_excluded_criteria_column(tmp_path, monkeypatch):
    import sqlite3

    import db

    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE roles (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, location TEXT,"
        " requirements TEXT NOT NULL, description TEXT NOT NULL,"
        " created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute("INSERT INTO roles (title, requirements, description) VALUES ('Old role', '[]', 'jd')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(db, "DB_PATH", path)

    db.init_db()

    assert db.list_roles()[0].excluded_criteria == []
