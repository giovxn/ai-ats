"""FastAPI app: the HTTP routes. Each route validates input, calls the LLM or the database, and returns JSON.

Run with:  uv run uvicorn main:app --reload
"""

from fastapi import FastAPI, HTTPException, UploadFile

import cvs
import db
import llm
import prompts
from schemas import Candidate, CVProfile, Role, RoleCreate, RoleExtraction, StageUpdate

app = FastAPI(title="OVI ATS")
db.init_db()


# ---------- Block 1: roles ----------

@app.post("/api/roles", status_code=201)
def create_role(body: RoleCreate) -> Role:
    """Paste a job description; the LLM extracts title, location and requirements; the role is saved."""
    try:
        extracted = llm.extract(prompts.ROLE_EXTRACTION, body.description, RoleExtraction)
    except llm.LLMError as error:
        raise HTTPException(status_code=502, detail=str(error))

    if not extracted.title.strip():
        raise HTTPException(
            status_code=422,
            detail="This doesn't look like a job description. Paste the full posting and try again.",
        )
    # Drop empty or punctuation-only items the model sometimes returns (seen: ["."]).
    extracted.excluded_criteria = [c.strip() for c in extracted.excluded_criteria if any(ch.isalnum() for ch in c)]
    return db.create_role(body.description, extracted)


@app.get("/api/roles")
def list_roles() -> list[Role]:
    return db.list_roles()


@app.get("/api/roles/{role_id}")
def get_role(role_id: int) -> Role:
    role = db.get_role(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found.")
    return role


# ---------- Block 2: candidates ----------

@app.post("/api/roles/{role_id}/candidates", status_code=201)
def upload_cv(role_id: int, file: UploadFile) -> Candidate:
    """Upload one CV (PDF or .txt) to a role. The LLM turns its text into a profile, which is saved.

    One file per request: the frontend sends several in parallel, so each file
    succeeds or fails on its own and shows its own progress.
    """
    if db.get_role(role_id) is None:
        raise HTTPException(status_code=404, detail="Role not found.")

    filename = file.filename or "cv"
    try:
        text = cvs.read_text(filename, file.file.read(cvs.MAX_FILE_BYTES + 1))
    except cvs.CVFileError as error:
        raise HTTPException(status_code=error.status, detail=str(error))

    # Checked before the LLM call, so a duplicate costs nothing.
    cv_hash = cvs.fingerprint(text)
    if db.candidate_exists(role_id, cv_hash):
        raise HTTPException(status_code=409, detail="This CV is already uploaded to this role.")

    try:
        profile = llm.extract(prompts.CV_PARSING, text, CVProfile)
    except llm.LLMError as error:
        raise HTTPException(status_code=502, detail=str(error))

    if not profile.is_cv:
        raise HTTPException(
            status_code=422,
            detail="This doesn't look like a CV. Check that you picked the right file.",
        )

    years = cvs.total_years(profile.jobs)
    try:
        return db.create_candidate(role_id, profile, years, filename, text, cv_hash)
    except db.DuplicateCV:
        raise HTTPException(status_code=409, detail="This CV is already uploaded to this role.")


@app.get("/api/roles/{role_id}/candidates")
def list_candidates(role_id: int) -> list[Candidate]:
    if db.get_role(role_id) is None:
        raise HTTPException(status_code=404, detail="Role not found.")
    return db.list_candidates(role_id)


@app.get("/api/candidates/{candidate_id}")
def get_candidate(candidate_id: int) -> Candidate:
    candidate = db.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return candidate


# ---------- Block 3: pipeline ----------

@app.patch("/api/candidates/{candidate_id}")
def move_candidate(candidate_id: int, body: StageUpdate) -> Candidate:
    """Move a candidate to another stage: {"stage": "shortlisted"}. Moving to the same stage is allowed."""
    candidate = db.update_stage(candidate_id, body.stage)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return candidate
