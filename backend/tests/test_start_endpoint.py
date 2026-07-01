def test_start_returns_session_and_question(client, valid_cv, valid_jd):
    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["first_question"]


def test_start_response_hides_plan_and_classification(client, valid_cv, valid_jd):
    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})
    body = response.json()
    # the payload exposes ONLY these fields — hidden state stays server-side
    assert set(body.keys()) == {"session_id", "first_question", "session_cost"}
    for leaked in ("plan", "interview_plan", "classification", "topics", "reasoning"):
        assert leaked not in body


def test_start_returns_session_cost(client, valid_cv, valid_jd):
    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})
    cost = response.json()["session_cost"]
    assert cost["turns"] == 1
    assert cost["is_stub"] is True
    assert cost["cost_usd"] == 0.0


def test_start_rejects_invalid_input(client, valid_jd):
    response = client.post("/start", json={"cv_text": "", "jd_text": valid_jd})
    assert response.status_code == 400


def test_start_returns_502_when_llm_fails(client, monkeypatch, valid_cv, valid_jd):
    def broken():
        raise RuntimeError("boom")

    monkeypatch.setattr("app.interview_engine.get_llm_client", broken)

    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})

    assert response.status_code == 502


def test_start_returns_500_when_misconfigured(client, monkeypatch, valid_cv, valid_jd):
    def missing_api_key():
        raise ValueError("OPENROUTER_API_KEY not set")

    monkeypatch.setattr("app.interview_engine.get_llm_client", missing_api_key)

    response = client.post("/start", json={"cv_text": valid_cv, "jd_text": valid_jd})

    assert response.status_code == 500
