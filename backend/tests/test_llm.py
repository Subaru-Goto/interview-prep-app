import pytest
from pydantic import BaseModel

from app.llm import FakeLLMClient
from app.schemas import Classification, InterviewPlan

MESSAGES = [{"role": "user", "content": "hello"}]


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
