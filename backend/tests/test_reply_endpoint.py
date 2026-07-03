def test_reply_returns_done_false_and_session_cost(client, started_session_id):
    response = client.post(
        "/reply", json={"session_id": started_session_id, "answer": "an answer"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["done"] is False
    assert "session_cost" in body


def test_stream_next_question_returns_token_and_done_events(
    client, started_session_id
):
    client.post(
        "/reply", json={"session_id": started_session_id, "answer": "an answer"}
    )

    response = client.get(f"/reply/{started_session_id}/stream")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"type": "token"' in response.text
    assert '"type": "done"' in response.text


def test_stream_next_question_unknown_session_returns_404(client):
    response = client.get("/reply/does-not-exist/stream")
    assert response.status_code == 404


def test_reply_session_cost_tracks_turns(client, started_session_id):
    before = client.post(
        "/reply", json={"session_id": started_session_id, "answer": "an answer"}
    ).json()["session_cost"]
    client.get(f"/reply/{started_session_id}/stream")  # populate the next question

    reply_response = client.post(
        "/reply", json={"session_id": started_session_id, "answer": "another answer"}
    )
    after = reply_response.json()["session_cost"]
    client.get(f"/reply/{started_session_id}/stream")

    assert after["turns"] == before["turns"] + 1
    assert before["is_stub"] is True and after["is_stub"] is True
    assert after["cost_usd"] == 0.0  # stub mode: placeholder zero, not omitted


def test_reply_rejects_empty_answer(client):
    response = client.post("/reply", json={"session_id": "irrelevant", "answer": "  "})
    assert response.status_code == 400


def test_reply_unknown_session_returns_404(client):
    response = client.post(
        "/reply", json={"session_id": "does-not-exist", "answer": "an answer"}
    )
    assert response.status_code == 404


def test_reply_returns_502_when_llm_fails(client, monkeypatch, started_session_id):
    def broken():
        raise RuntimeError("boom")

    monkeypatch.setattr("app.interview_engine.get_llm_client", broken)

    response = client.post(
        "/reply", json={"session_id": started_session_id, "answer": "an answer"}
    )

    assert response.status_code == 502


def test_reply_returns_500_when_misconfigured(client, monkeypatch, started_session_id):
    def missing_api_key():
        raise ValueError("OPENROUTER_API_KEY not set")

    monkeypatch.setattr("app.interview_engine.get_llm_client", missing_api_key)

    response = client.post(
        "/reply", json={"session_id": started_session_id, "answer": "an answer"}
    )

    assert response.status_code == 500
