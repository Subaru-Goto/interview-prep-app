import pytest

from app.config import settings
from app.llm import get_llm_client


@pytest.fixture(autouse=True)
def force_stub_mode(monkeypatch):
    """Force the fake LLM for every test so they stay deterministic (no network)."""
    monkeypatch.setattr(settings, "use_fake_llm", True)
    get_llm_client.cache_clear()


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
