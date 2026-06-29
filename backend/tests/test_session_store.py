import pytest

from app.schemas import (
    Classification,
    InterviewPlan,
    InterviewTopic,
    Message,
    Session,
)
from app.session_store import InMemorySessionStore, SessionNotFound


@pytest.fixture
def store():
    """A fresh, empty store for each test (isolation)."""
    return InMemorySessionStore()


def make_session(session_id: str = "s1", content: str = "First question?") -> Session:
    """Build a valid Session so tests don't repeat the construction."""
    return Session(
        session_id=session_id,
        classification=Classification(
            interview_type="technical_analytical", seniority="senior"
        ),
        interview_plan=InterviewPlan(
            reasoning="strong backend, JD needs scale",
            topics=[InterviewTopic(title=f"T{i}", focus="f") for i in range(5)],
        ),
        transcript=[Message(role="assistant", content=content)],
    )


def test_save_then_get_returns_same_session(store):
    session = make_session()
    store.save(session)
    retrieved = store.get(session.session_id)
    assert retrieved == session


def test_get_missing_raises(store):
    with pytest.raises(SessionNotFound):
        store.get("missing-id")


def test_save_overwrites_existing(store):
    store.save(make_session("s1", content="Q1"))
    # Overwrite with the same session.id
    store.save(make_session("s1", content="Q2"))
    assert store.get("s1").transcript[0].content == "Q2"

