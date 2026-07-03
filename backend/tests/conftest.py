import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.llm import get_llm_client
from app.main import app


@pytest.fixture(autouse=True)
def force_stub_mode(monkeypatch):
    """Force the fake LLM for every test so they stay deterministic (no network)."""
    monkeypatch.setattr(settings, "use_fake_llm", True)
    get_llm_client.cache_clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def started_session_id(client, valid_cv, valid_jd):
    """A session_id with its opening question already asked (via /start then
    draining GET /start/{id}/stream), for tests that need an existing,
    ready-to-reply-to session but don't care how it was created."""
    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})
    session_id = response.json()["session_id"]
    client.get(f"/start/{session_id}/stream")
    return session_id


@pytest.fixture
def valid_cv():
    return (
        "Experienced backend engineer with several years building and scaling "
        "Python services. Led code reviews, mentored junior developers, and "
        "owned production systems across multiple teams."
    )


@pytest.fixture
def valid_jd():
    return (
        "We are hiring a Senior Backend Engineer to design and scale distributed "
        "systems. You will own services end to end, mentor engineers, and drive "
        "architectural decisions. Strong Python and systems experience required. "
    ) * 3
