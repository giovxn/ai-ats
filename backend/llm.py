"""The one place the app talks to OpenAI.

Every AI feature goes through `extract()`: give it a prompt (from prompts.py),
the input text and a Pydantic schema (from schemas.py), and you get back a
validated object of that schema, or an LLMError with a readable message.
To add a new AI feature: write a prompt, define its output schema, call extract()
from a route in main.py.
"""

import logging
import os
from pathlib import Path
from typing import TypeVar

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from pydantic import BaseModel

load_dotenv(Path(__file__).parent.parent / ".env")

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

# An extraction takes 3 to 7 seconds. Without a limit the SDK waits up to 10 minutes,
# so give up after 30 seconds and retry once: about a minute at worst.
TIMEOUT_SECONDS = 30
MAX_RETRIES = 1

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger("uvicorn.error")  # uvicorn's logger, so errors show in its terminal


class LLMError(Exception):
    """Raised when the model can't give us a valid answer. The message is shown to the user."""


def extract(instructions: str, text: str, schema: type[T]) -> T:
    if not os.getenv("OPENAI_API_KEY"):
        raise LLMError("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")

    try:
        response = OpenAI(timeout=TIMEOUT_SECONDS, max_retries=MAX_RETRIES).responses.parse(
            model=MODEL,
            instructions=instructions,
            input=text,
            text_format=schema,  # OpenAI must answer in this JSON schema
        )
    except OpenAIError as error:
        # The raw error goes to the backend log; the user gets a plain message.
        logger.error("OpenAI call failed: %r", error)
        raise LLMError(_user_message(error)) from error
    except ValueError as error:
        # Invalid JSON, or JSON that doesn't match the schema (Pydantic ValidationError).
        raise LLMError("The AI returned data in an unexpected format.") from error

    parsed = response.output_parsed
    if parsed is None:  # e.g. the model refused, or returned no text
        raise LLMError("The AI didn't return a usable answer.")
    return parsed


def _user_message(error: OpenAIError) -> str:
    """Turn an OpenAI error into a message that says what to do next."""
    if isinstance(error, APITimeoutError):  # check before APIConnectionError, its parent
        return "The AI took too long to answer. Try again."
    if isinstance(error, APIConnectionError):
        return "Unable to reach the AI service. Check your internet connection and try again."
    if isinstance(error, AuthenticationError):
        return "OpenAI rejected the API key. Check OPENAI_API_KEY in .env, then restart the backend."
    if isinstance(error, RateLimitError):
        return "The AI service is busy or out of credit. Wait a minute and try again, or check your OpenAI billing."
    return "The AI service failed. Try again in a moment."
