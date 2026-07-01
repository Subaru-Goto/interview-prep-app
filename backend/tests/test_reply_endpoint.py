from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _start_session(valid_cv, valid_jd):
    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})
    return response.json()["session_id"]


def test_reply_returns_next_question(valid_cv, valid_jd):
    session_id = _start_session(valid_cv, valid_jd)

    response = client.post(
        "/reply", json={"session_id": session_id, "answer": "an answer"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["done"] is False
    assert body["next_question"]


def test_reply_rejects_empty_answer():
    response = client.post("/reply", json={"session_id": "irrelevant", "answer": "  "})
    assert response.status_code == 400


def test_reply_unknown_session_returns_404():
    response = client.post(
        "/reply", json={"session_id": "does-not-exist", "answer": "an answer"}
    )
    assert response.status_code == 404


def test_reply_returns_502_when_llm_fails(monkeypatch, valid_cv, valid_jd):
    session_id = _start_session(valid_cv, valid_jd)

    def broken():
        raise RuntimeError("boom")

    monkeypatch.setattr("app.interview_engine.get_llm_client", broken)

    response = client.post(
        "/reply", json={"session_id": session_id, "answer": "an answer"}
    )

    assert response.status_code == 502
