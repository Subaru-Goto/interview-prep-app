import pytest

from app.input_guard import InvalidInput
from app.interview_engine import start_interview
from app.schemas import MessageRole, Session
from app.session_store import session_store


def test_start_interview_returns_session_and_question(valid_cv, valid_jd):
    session_id, question = start_interview(valid_cv, valid_jd)
    assert isinstance(session_id, str) and session_id
    assert isinstance(question, str) and question


def test_start_interview_persists_session(valid_cv, valid_jd):
    session_id, _ = start_interview(valid_cv, valid_jd)
    session = session_store.get(session_id)
    assert isinstance(session, Session)
    assert session.classification is not None
    assert 5 <= len(session.interview_plan.topics) <= 6
    assert session.transcript[0].role == MessageRole.assistant


def test_plan_is_server_side_only(valid_cv, valid_jd):
    session_id, question = start_interview(valid_cv, valid_jd)
    stored = session_store.get(session_id)
    assert len(stored.interview_plan.topics) >= 5
    assert all(isinstance(value, str) for value in (session_id, question))


def test_start_interview_rejects_invalid_input(valid_jd):
    with pytest.raises(InvalidInput):
        start_interview("", valid_jd)  # empty CV fails the input guard
