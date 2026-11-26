"""Data shapes, validated by Pydantic.

Two kinds live here:
- LLM outputs: the exact JSON the model must return (sent to OpenAI as the schema).
- API models: what the endpoints accept and return.
"""

from typing import Annotated, Literal

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
    excluded_criteria: list[str]  # e.g. "Male candidates only": flagged to the recruiter, never used


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


# Block 4: evidence for each requirement (prompts.EVIDENCE). Numbers are 1-based, as the model sees them.
EvidenceStatus = Literal["demonstrated", "partial", "not_found"]  # describes the CV, not the person
EvidenceTag = Literal["duty", "action", "outcome"]  # one quote can be several


class EvidenceQuote(BaseModel):
    text: str  # copied word for word from the CV; checked by code before it's trusted
    job_number: int | None  # the job it's written under; null for the summary, skills, a course...
    tags: list[EvidenceTag]


class RequirementEvidence(BaseModel):
    requirement_number: int
    status: EvidenceStatus
    quotes: list[EvidenceQuote]


class HighlightTags(BaseModel):
    """Tags for one bullet of job 1 or 2, the jobs shown on the scan card."""
    job_number: int
    highlight_number: int
    tags: list[EvidenceTag]


class EvidenceExtraction(BaseModel):
    requirements: list[RequirementEvidence]
    recent_highlights: list[HighlightTags]


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
    excluded_criteria: list[str]
    description: str
    created_at: str


# The four pipeline stages. The database has the same list as a CHECK rule.
Stage = Literal["new", "shortlisted", "interview", "rejected"]


class StageUpdate(BaseModel):
    stage: Stage  # anything else is rejected with 422 before the route runs


# What the API returns about evidence. Built by evidence.py (plain code) from the stored AI output.
class QuoteView(BaseModel):
    text: str
    job_index: int | None  # 0-based position in Candidate.jobs (most recent first)
    tags: list[EvidenceTag]
    verified: bool  # found in the CV text, inside that job's section


# What the app shows. "unverified": the AI said the CV shows it, but none of its quotes could be
# matched to the CV text, so it's never shown as found.
ShownStatus = Literal["demonstrated", "partial", "not_found", "unverified"]


class RequirementView(BaseModel):
    text: str
    must_have: bool
    status: ShownStatus
    quotes: list[QuoteView]
    # A must-have with verified evidence only in jobs older than the 2 on the scan card.
    buried: bool


class EvidenceView(BaseModel):
    requirements: list[RequirementView]
    highlight_tags: list[list[list[EvidenceTag]]]  # [job 1, job 2] -> one tag list per highlight
    sections_found: bool  # False: the jobs couldn't be located in the CV text, so nothing is verified


# pending: not checked yet. failed: the AI call failed; it can be retried.
EvidenceState = Literal["pending", "complete", "failed"]


class Candidate(BaseModel):
    id: int
    role_id: int
    stage: Stage
    name: str | None
    current_title: str | None
    years_experience: float | None  # counted by cvs.total_years, not by the LLM
    skills: list[str]
    jobs: list[Job]
    education: list[Education]
    summary: str
    cv_filename: str
    cv_text: str  # the text we extracted from the file, so a person can check the profile
    # Found in cv_text by code (cvs.py), not by the AI, so a recruiter can contact and check the candidate.
    email: str | None
    phone: str | None
    links: list[str]  # LinkedIn, GitHub, a portfolio...
    evidence_status: EvidenceState
    evidence: EvidenceView | None  # None unless evidence_status is "complete"
    created_at: str


# Block 4: the decision log. Rows are only added, never changed or deleted.
PromptChoice = Literal["look_again", "reject_anyway"]


class DecisionCreate(BaseModel):
    to_stage: Stage
    prompt_shown: bool = False  # the "Before you reject" check appeared
    prompt_choice: PromptChoice | None = None
    undo_of: int | None = None  # the decision this one reverses


class Decision(BaseModel):
    id: int
    candidate_id: int
    from_stage: Stage
    to_stage: Stage
    prompt_shown: bool
    prompt_choice: PromptChoice | None
    undo_of: int | None
    created_at: str


class DecisionResult(BaseModel):
    candidate: Candidate
    decision: Decision
