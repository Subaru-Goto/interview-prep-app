from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _start_session(valid_cv, valid_jd):
    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})
    return response.json()["session_id"]


def test_finish_returns_scorecard(valid_cv, valid_jd):
    session_id = _start_session(valid_cv, valid_jd)

    response = client.post("/finish", json={"session_id": session_id})

    assert response.status_code == 200
    body = response.json()
    assert 5 <= len(body["topic_scores"]) <= 6
    assert body["overall_assessment"]
    assert len(body["strengths"]) >= 2
    assert len(body["gaps"]) >= 2
    assert body["focus_recommendation"]


def test_finish_works_after_a_reply(valid_cv, valid_jd):
    session_id = _start_session(valid_cv, valid_jd)
    client.post("/reply", json={"session_id": session_id, "answer": "an answer"})

    response = client.post("/finish", json={"session_id": session_id})

    assert response.status_code == 200


def test_finish_unknown_session_returns_404():
    response = client.post("/finish", json={"session_id": "does-not-exist"})
    assert response.status_code == 404
