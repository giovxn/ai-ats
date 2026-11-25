"""The one place the app talks to OpenAI.

Every AI feature goes through `extract()`: give it a prompt (from prompts.py),
the input text and a Pydantic schema (from schemas.py), and you get back a
validated object of that schema, or an LLMError with a readable message.
To add a new AI feature: write a prompt, define its output schema, call extract()
from a route in main.py.
"""

import os
from pathlib import Path
from typing import TypeVar

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel

load_dotenv(Path(__file__).parent.parent / ".env")

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when the model can't give us a valid answer. The message is shown to the user."""


def extract(instructions: str, text: str, schema: type[T]) -> T:
    if not os.getenv("OPENAI_API_KEY"):
        raise LLMError("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")

    try:
        response = OpenAI().responses.parse(
            model=MODEL,
            instructions=instructions,
            input=text,
            text_format=schema,  # OpenAI must answer in this JSON schema
        )
    except OpenAIError as error:
        raise LLMError(f"The AI service failed: {error}") from error
    except ValueError as error:
        # Invalid JSON, or JSON that doesn't match the schema (Pydantic ValidationError).
        raise LLMError("The AI returned data in an unexpected format.") from error

    parsed = response.output_parsed
    if parsed is None:  # e.g. the model refused, or returned no text
        raise LLMError("The AI didn't return a usable answer.")
    return parsed
