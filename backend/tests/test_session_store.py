import pytest

from app.config import settings
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


@pytest.fixture
def clock():
    """A fake clock the test controls directly, so TTL tests don't sleep."""
    current = [1_000_000.0]

    def time_fn():
        return current[0]

    time_fn.current = current
    return time_fn


@pytest.fixture
def store_with_clock(clock):
    return InMemorySessionStore(time_fn=clock), clock


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


def test_delete_removes_session(store):
    store.save(make_session())
    store.delete("s1")
    with pytest.raises(SessionNotFound):
        store.get("s1")


def test_delete_missing_id_is_a_no_op(store):
    store.delete("does-not-exist")  # should not raise


def test_get_expires_session_after_ttl(store_with_clock, monkeypatch):
    store, clock = store_with_clock
    monkeypatch.setattr(settings, "session_ttl_seconds", 60)
    store.save(make_session())

    clock.current[0] += 61  # just past the TTL

    with pytest.raises(SessionNotFound):
        store.get("s1")


def test_get_refreshes_ttl_on_access(store_with_clock, monkeypatch):
    store, clock = store_with_clock
    monkeypatch.setattr(settings, "session_ttl_seconds", 60)
    store.save(make_session())

    clock.current[0] += 40  # under the TTL
    store.get("s1")  # touches the session, resets its clock

    clock.current[0] += 40  # would be 80s since save, but only 40s since the touch
    store.get("s1")  # still alive


def test_save_evicts_least_recently_active_over_cap(store_with_clock, monkeypatch):
    store, clock = store_with_clock
    monkeypatch.setattr(settings, "max_sessions", 2)

    store.save(make_session("s1"))
    clock.current[0] += 1
    store.save(make_session("s2"))
    clock.current[0] += 1
    store.save(make_session("s3"))  # pushes the store over the cap

    with pytest.raises(SessionNotFound):
        store.get("s1")  # oldest, least recently active — evicted
    assert store.get("s2")
    assert store.get("s3")

