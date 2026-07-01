def test_finish_returns_scorecard_after_a_reply(client, started_session_id):
    client.post(
        "/reply", json={"session_id": started_session_id, "answer": "an answer"}
    )

    response = client.post("/finish", json={"session_id": started_session_id})

    assert response.status_code == 200
    body = response.json()
    assert 5 <= len(body["topic_scores"]) <= 6
    assert body["overall_assessment"]
    assert len(body["strengths"]) >= 2
    assert len(body["gaps"]) >= 2
    assert body["focus_recommendation"]


def test_finish_with_no_answers_returns_400(client, started_session_id):
    response = client.post("/finish", json={"session_id": started_session_id})

    assert response.status_code == 400


def test_finish_unknown_session_returns_404(client):
    response = client.post("/finish", json={"session_id": "does-not-exist"})
    assert response.status_code == 404
