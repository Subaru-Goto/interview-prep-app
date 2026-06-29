import pytest

from app.config import settings
from app.input_guard import InvalidInput
from app.interview_engine import start_interview
from app.llm import get_llm_client
from app.schemas import MessageRole, Session
from app.session_store import session_store

VALID_CV = (
    "Experienced backend engineer with several years building and scaling "
    "Python services. Led code reviews, mentored junior developers, and "
    "owned production systems across multiple teams."
)
VALID_JD = (
    "We are hiring a Senior Backend Engineer to design and scale distributed "
    "systems. Role Overview: You will own services end to end, mentor engineers, and drive "
    "architectural decisions. Strong Python and systems experience required. "
) * 3


@pytest.fixture(autouse=True)
def force_stub_mode(monkeypatch):
    """Run the engine against the fake LLM so tests are deterministic."""
    monkeypatch.setattr(settings, "use_fake_llm", True)
    get_llm_client.cache_clear()


def test_start_interview_returns_session_and_question():
    session_id, question = start_interview(VALID_CV, VALID_JD)
    assert isinstance(session_id, str) and session_id
    assert isinstance(question, str) and question


def test_start_interview_persists_session():
    session_id, _ = start_interview(VALID_CV, VALID_JD)
    session = session_store.get(session_id)
    assert isinstance(session, Session)
    assert session.classification is not None
    assert 5 <= len(session.interview_plan.topics) <= 6
    assert session.transcript[0].role == MessageRole.assistant


def test_plan_is_server_side_only():
    session_id, question = start_interview(VALID_CV, VALID_JD)
    stored = session_store.get(session_id)
    assert len(stored.interview_plan.topics) >= 5
    assert all(isinstance(value, str) for value in (session_id, question))


def test_start_interview_rejects_invalid_input():
    with pytest.raises(InvalidInput):
        start_interview("", VALID_JD)
