import pytest

from app.config import settings
from app.input_guard import InvalidInput
from app.interview_engine import (
    Transition,
    reply,
    resolve_transition,
    start_interview,
)
from app.schemas import InterviewerAction, MessageRole, Session
from app.session_store import SessionNotFound, session_store


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