"""Data shapes, validated by Pydantic.

Two kinds live here:
- LLM outputs: the exact JSON the model must return (sent to OpenAI as the schema).
- API models: what the endpoints accept and return.
"""

from pydantic import BaseModel, Field


# ---------- LLM outputs ----------

class Requirement(BaseModel):
    text: str
    must_have: bool


class RoleExtraction(BaseModel):
    """What the LLM pulls out of a job description (prompts.ROLE_EXTRACTION)."""
    title: str
    location: str | None
    requirements: list[Requirement]


# ---------- API ----------

class RoleCreate(BaseModel):
    # Bounds keep out empty submissions and very large pastes (cost and latency).
    description: str = Field(min_length=50, max_length=20_000)


class Role(BaseModel):
    id: int
    title: str
    location: str | None
    requirements: list[Requirement]
    description: str
    created_at: str
