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
