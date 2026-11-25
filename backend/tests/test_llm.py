"""Unit tests for llm.extract: each OpenAI failure becomes an LLMError with a readable message."""

from types import SimpleNamespace

import httpx2
import pytest
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAIError,
    RateLimitError,
)

import llm
from schemas import RoleExtraction


def fake_openai(monkeypatch, *, returns=None, raises=None):
    """Replace the OpenAI client so responses.parse returns or raises what the test needs."""

    def parse(**kwargs):
        if raises:
            raise raises
        return SimpleNamespace(output_parsed=returns)

    client = SimpleNamespace(responses=SimpleNamespace(parse=parse), options={})

    def make_client(**options):
        client.options = options  # so tests can check the timeout and retries
        return client

    monkeypatch.setattr(llm, "OpenAI", make_client)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return client


REQUEST = httpx2.Request("POST", "https://api.openai.com/v1/responses")


def http_error(error_class, status):
    """Build the error the SDK raises for an HTTP status, with a raw message we must not show."""
    response = httpx2.Response(status, request=REQUEST)
    return error_class("raw details sk-proj-****abcd", response=response, body=None)


def test_returns_the_parsed_object(monkeypatch):
    expected = RoleExtraction(title="Senior Accountant", location=None, requirements=[])
    fake_openai(monkeypatch, returns=expected)

    assert llm.extract("instructions", "text", RoleExtraction) == expected


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(llm.LLMError, match="OPENAI_API_KEY is not set"):
        llm.extract("instructions", "text", RoleExtraction)


def test_client_has_a_timeout_and_one_retry(monkeypatch):
    client = fake_openai(monkeypatch, returns=RoleExtraction(title="x", location=None, requirements=[]))

    llm.extract("instructions", "text", RoleExtraction)

    assert client.options == {"timeout": 30, "max_retries": 1}


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (APITimeoutError(request=REQUEST), "took too long"),
        (APIConnectionError(request=REQUEST), "Unable to reach the AI service"),
        (http_error(AuthenticationError, 401), "rejected the API key"),
        (http_error(RateLimitError, 429), "busy or out of credit"),
        (http_error(BadRequestError, 400), "The AI service failed. Try again"),
        (OpenAIError("raw details sk-proj-****abcd"), "The AI service failed. Try again"),
    ],
)
def test_openai_errors_become_plain_messages(monkeypatch, caplog, error, message):
    fake_openai(monkeypatch, raises=error)

    with pytest.raises(llm.LLMError, match=message) as raised:
        llm.extract("instructions", "text", RoleExtraction)

    # The raw error (which can include part of the key) is logged, never shown.
    assert "raw details" not in str(raised.value) and "sk-" not in str(raised.value)
    assert "OpenAI call failed" in caplog.text


def test_output_that_does_not_match_the_schema(monkeypatch):
    # Pydantic's ValidationError is a ValueError, which is what parse raises on bad JSON.
    fake_openai(monkeypatch, raises=ValueError("invalid json"))

    with pytest.raises(llm.LLMError, match="unexpected format"):
        llm.extract("instructions", "text", RoleExtraction)


def test_refusal_or_empty_answer(monkeypatch):
    fake_openai(monkeypatch, returns=None)

    with pytest.raises(llm.LLMError, match="didn't return a usable answer"):
        llm.extract("instructions", "text", RoleExtraction)
