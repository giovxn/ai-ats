"""Shared test setup: every test gets an empty temporary database and never calls OpenAI."""

import pytest
from fastapi.testclient import TestClient

import db
import llm
import main
from schemas import CVProfile, Education, Job, Requirement, RoleExtraction

JD = "We're hiring a Senior Accountant in Abu Dhabi to lead the month-end close and reporting."


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point the app at a fresh SQLite file, so tests never touch ats.db."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def fake_llm(monkeypatch):
    """Replace llm.extract with a fake. Set .result / .cv_result (or .error) per test; .calls counts calls."""

    class FakeLLM:
        result = RoleExtraction(
            title="Senior Accountant",
            location="Abu Dhabi, UAE",
            requirements=[
                Requirement(text="ACCA, CPA or CA", must_have=True),
                Requirement(text="NetSuite experience", must_have=False),
            ],
            excluded_criteria=[],
        )
        cv_result = CVProfile(
            is_cv=True,
            name="Fatima Khoury",
            current_title="Financial Controller",
            skills=["IFRS", "ACCA", "NetSuite"],
            jobs=[
                Job(title="Financial Controller", company="Gulfway Freight", start="2021-05",
                    end=None, is_current=True, highlights=["Consolidation of 9 entities"]),
                Job(title="Senior Associate", company="EY", start="2017-09", end="2021-04",
                    is_current=False, highlights=[]),
            ],
            education=[Education(qualification="BBA Accounting", institution="LAU", year="2015")],
            summary="Finance leader with audit and group reporting experience.",
        )
        error: Exception | None = None
        calls = 0

        def extract(self, instructions, text, schema):
            self.calls += 1
            if self.error:
                raise self.error
            return self.cv_result if schema is CVProfile else self.result

    fake = FakeLLM()
    monkeypatch.setattr(llm, "extract", fake.extract)
    return fake
