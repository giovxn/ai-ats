"""FastAPI app: the HTTP routes. Each route validates input, calls the LLM or the database, and returns JSON.

Run with:  uv run uvicorn main:app --reload
"""

from fastapi import FastAPI, HTTPException

import db
import llm
import prompts
from schemas import Role, RoleCreate, RoleExtraction

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
