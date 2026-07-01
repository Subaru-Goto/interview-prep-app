def test_finish_returns_scorecard_after_a_reply(client, started_session_id):
    client.post(
        "/reply", json={"session_id": started_session_id, "answer": "an answer"}
    )

    response = client.post("/finish", json={"session_id": started_session_id})

    assert response.status_code == 200
    body = response.json()
    scorecard = body["scorecard"]
    assert 5 <= len(scorecard["topic_scores"]) <= 6
    assert scorecard["overall_assessment"]
    assert len(scorecard["strengths"]) >= 2
    assert len(scorecard["gaps"]) >= 2
    assert scorecard["focus_recommendation"]


def test_finish_returns_session_cost(client, started_session_id):
    client.post(
        "/reply", json={"session_id": started_session_id, "answer": "an answer"}
    )

    response = client.post("/finish", json={"session_id": started_session_id})

    cost = response.json()["session_cost"]
    assert cost["turns"] == 2  # opening question + one follow-up/advance question
    assert cost["is_stub"] is True
    assert cost["cost_usd"] == 0.0


def test_finish_with_no_answers_returns_400(client, started_session_id):
    response = client.post("/finish", json={"session_id": started_session_id})

    assert response.status_code == 400


def test_finish_unknown_session_returns_404(client):
    response = client.post("/finish", json={"session_id": "does-not-exist"})
    assert response.status_code == 404
