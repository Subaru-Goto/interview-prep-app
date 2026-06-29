from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_start_returns_session_and_question(valid_cv, valid_jd):
    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["first_question"]


def test_start_response_hides_plan_and_classification(valid_cv, valid_jd):
    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})
    body = response.json()
    # the payload exposes ONLY these two fields — hidden state stays server-side
    assert set(body.keys()) == {"session_id", "first_question"}
    for leaked in ("plan", "interview_plan", "classification", "topics", "reasoning"):
        assert leaked not in body


def test_start_rejects_invalid_input(valid_jd):
    response = client.post("/start", json={"cv_text": "", "jd_text": valid_jd})
    assert response.status_code == 400
