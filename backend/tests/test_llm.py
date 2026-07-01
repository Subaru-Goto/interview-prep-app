from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.config import settings
from app.llm import FakeLLMClient, OpenRouterLLMClient
from app.schemas import Classification, InterviewPlan

MESSAGES = [{"role": "user", "content": "hello"}]


def _fake_response(content=None, usage_extra=None):
    usage = SimpleNamespace(
        prompt_tokens=10, completion_tokens=5, **(usage_extra or {})
    )
    message = SimpleNamespace(content=content, parsed=None)
    return SimpleNamespace(usage=usage, choices=[SimpleNamespace(message=message)])


@pytest.fixture
def client():
    """A fresh fake client for each test."""
    return FakeLLMClient()


def test_text_call_echoes_and_has_no_parsed(client):
    result = client.complete(MESSAGES)
    assert result.content is not None
    assert result.parsed is None


def test_classification_call_returns_validated_classification(client):
    result = client.complete(MESSAGES, response_schema=Classification)
    assert isinstance(result.parsed, Classification)
    assert result.content is None


def test_plan_call_returns_validated_plan(client):
    result = client.complete(MESSAGES, response_schema=InterviewPlan)
    assert isinstance(result.parsed, InterviewPlan)
    assert 5 <= len(result.parsed.topics) <= 6


def test_unknown_schema_raises(client):
    class Unknown(BaseModel):
        pass

    with pytest.raises(ValueError):
        client.complete(MESSAGES, response_schema=Unknown)


def test_openrouter_client_captures_cost_from_usage(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    real_client = OpenRouterLLMClient()
    monkeypatch.setattr(
        real_client.client.chat.completions,
        "create",
        lambda **kwargs: _fake_response(content="hi", usage_extra={"cost": 0.0042}),
    )

    result = real_client.complete(MESSAGES)

    assert result.usage.prompt_tokens == 10
    assert result.usage.completion_tokens == 5
    assert result.usage.cost == pytest.approx(0.0042)


def test_openrouter_client_defaults_cost_to_zero_when_absent(monkeypatch):
    """Defensive: OpenRouter always sets `cost` now, but it's an extra field
    the OpenAI SDK's typed usage model doesn't declare — don't blow up if a
    proxied/non-OpenRouter response leaves it off."""
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    real_client = OpenRouterLLMClient()
    monkeypatch.setattr(
        real_client.client.chat.completions,
        "create",
        lambda **kwargs: _fake_response(content="hi"),
    )

    result = real_client.complete(MESSAGES)

    assert result.usage.cost == 0.0
