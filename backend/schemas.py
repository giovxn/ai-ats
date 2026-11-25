"""Data shapes, validated by Pydantic.

Two kinds live here:
- LLM outputs: the exact JSON the model must return (sent to OpenAI as the schema).
- API models: what the endpoints accept and return.
"""

from typing import Annotated

from pydantic import BaseModel, StringConstraints


# ---------- LLM outputs ----------

class Requirement(BaseModel):
    text: str
    must_have: bool


class RoleExtraction(BaseModel):
    """What the LLM pulls out of a job description (prompts.ROLE_EXTRACTION)."""
    title: str
    location: str | None
    requirements: list[Requirement]


class Job(BaseModel):
    """One role in a candidate's work history."""
    title: str
    company: str | None
    start: str | None  # "YYYY-MM", or "YYYY" when the CV gives only the year
    end: str | None    # null for a current role, or when the CV doesn't say
    is_current: bool
    highlights: list[str]


class Education(BaseModel):
    qualification: str  # e.g. "BSc Accounting"
    institution: str | None
    year: str | None


class CVProfile(BaseModel):
    """What the LLM pulls out of a CV (prompts.CV_PARSING)."""
    is_cv: bool
    name: str | None
    current_title: str | None
    skills: list[str]
    jobs: list[Job]
    education: list[Education]
    summary: str


# ---------- API ----------

class RoleCreate(BaseModel):
    # Bounds keep out empty submissions and very large pastes (cost and latency).
    # Whitespace is stripped first, so padding can't sneak past the minimum.
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=50, max_length=20_000)]


class Role(BaseModel):
    id: int
    title: str
    location: str | None
    requirements: list[Requirement]
    description: str
    created_at: str


class Candidate(BaseModel):
    id: int
    role_id: int
    stage: str  # new, shortlisted, interview or rejected (moved in Block 3)
    name: str | None
    current_title: str | None
    years_experience: float | None  # counted by cvs.total_years, not by the LLM
    skills: list[str]
    jobs: list[Job]
    education: list[Education]
    summary: str
    cv_filename: str
    cv_text: str  # the text we extracted from the file, so a person can check the profile
    created_at: str
