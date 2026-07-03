import json

import pytest

from app.config import settings
from app.input_guard import InvalidInput
from app.interview_engine import (
    Transition,
    _accumulate_usage,
    _build_interviewer_messages,
    _build_judge_messages,
    decide_and_advance,
    finish_interview,
    get_session_cost,
    start_interview,
    stream_first_question,
    stream_reply_question,
)
from app.llm import Usage
from app.prompts import JUDGE_ANTI_INJECTION_GUARD, STAY_ON_TASK_GUARD
from app.schemas import MessageRole, Scorecard, Session
from app.session_store import SessionNotFound, session_store


def _drain_first_question(session_id: str) -> str:
    """Consume stream_first_question's SSE events, returning the full
    question text assembled from its 'token' events."""
    text = ""
    for event in stream_first_question(session_id):
        payload = json.loads(event.removeprefix("data: ").strip())
        if payload["type"] == "token":
            text += payload["text"]
    return text


def _start_and_ask(cv_text: str, jd_text: str) -> tuple[str, str]:
    """Run the full two-step start flow (start_interview + drain
    stream_first_question) for tests that just need a ready session with
    its opening question already in the transcript."""
    session_id = start_interview(cv_text, jd_text)
    return session_id, _drain_first_question(session_id)


def _drain_reply_question(session_id: str) -> str:
    """Consume stream_reply_question's SSE events, returning the full
    question text assembled from its 'token' events."""
    text = ""
    for event in stream_reply_question(session_id):
        payload = json.loads(event.removeprefix("data: ").strip())
        if payload["type"] == "token":
            text += payload["text"]
    return text


def _answer(session_id: str, answer: str) -> tuple[bool, str | None]:
    """Run a full reply turn (decide_and_advance + drain the question
    stream unless the interview just finished) and return (done, question),
    for tests that don't care how the work is split across the two calls."""
    outcome = decide_and_advance(session_id, answer)
    if outcome == Transition.finish:
        return True, None
    return False, _drain_reply_question(session_id)


def test_start_interview_returns_session_id_with_empty_transcript(valid_cv, valid_jd):
    session_id = start_interview(valid_cv, valid_jd)
    assert isinstance(session_id, str) and session_id
    assert session_store.get(session_id).transcript == []


def test_start_interview_persists_session(valid_cv, valid_jd):
    session_id = start_interview(valid_cv, valid_jd)
    session = session_store.get(session_id)
    assert isinstance(session, Session)
    assert session.classification is not None
    assert 5 <= len(session.interview_plan.topics) <= 6


def test_plan_is_server_side_only(valid_cv, valid_jd):
    session_id = start_interview(valid_cv, valid_jd)
    stored = session_store.get(session_id)
    assert len(stored.interview_plan.topics) >= 5


def test_start_interview_rejects_invalid_input(valid_jd):
    with pytest.raises(InvalidInput):
        start_interview("", valid_jd)


def test_stream_first_question_yields_token_then_done_events(valid_cv, valid_jd):
    session_id = start_interview(valid_cv, valid_jd)
    events = [
        json.loads(e.removeprefix("data: ").strip())
        for e in stream_first_question(session_id)
    ]

    token_events = [e for e in events if e["type"] == "token"]
    assert token_events
    assert "".join(e["text"] for e in token_events)

    assert events[-1]["type"] == "done"
    assert "session_cost" in events[-1]


def test_stream_first_question_appends_to_transcript(valid_cv, valid_jd):
    session_id = start_interview(valid_cv, valid_jd)
    question = _drain_first_question(session_id)

    transcript = session_store.get(session_id).transcript
    assert len(transcript) == 1
    assert transcript[0].role == MessageRole.assistant
    assert transcript[0].content == question


def test_stream_first_question_unknown_session_raises():
    with pytest.raises(SessionNotFound):
        list(stream_first_question("does-not-exist"))


def _assistant_count(session):
    return sum(1 for m in session.transcript if m.role == MessageRole.assistant)


def test_reply_returns_next_question_and_appends(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    before = len(session_store.get(session_id).transcript)

    done, question = _answer(session_id, "A reasonable answer about the topic.")

    assert done is False
    assert isinstance(question, str) and question
    transcript = session_store.get(session_id).transcript
    # one candidate answer + one new question appended
    assert len(transcript) == before + 2
    assert transcript[-2].role == MessageRole.user
    assert transcript[-1].role == MessageRole.assistant


def test_reply_enforces_one_followup_then_advances(valid_cv, valid_jd):
    # the stub always proposes follow_up, so the engine's limit is what advances
    session_id, _ = _start_and_ask(valid_cv, valid_jd)

    _answer(session_id, "first answer")
    session = session_store.get(session_id)
    assert session.followups_asked == 1     # probed the current topic
    assert session.current_topic_index == 0  # stayed on the same topic

    _answer(session_id, "second answer")
    session = session_store.get(session_id)
    assert session.current_topic_index == 1  # engine forced the advance
    assert session.followups_asked == 0      # counter reset on advance


def test_interviewer_prompt_includes_stay_on_task_guard(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    session = session_store.get(session_id)

    system = _build_interviewer_messages(session)[0]["content"]

    assert STAY_ON_TASK_GUARD in system


def test_judge_prompt_includes_anti_injection_guard(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    _answer(session_id, "first answer")
    session = session_store.get(session_id)

    system = _build_judge_messages(session)[0]["content"]

    assert JUDGE_ANTI_INJECTION_GUARD in system


def test_reply_is_bounded_and_finishes(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)

    done = False
    for _ in range(50):  # safety bound; should finish well before this
        done, _ = _answer(session_id, "an answer")
        if done:
            break

    assert done is True
    session = session_store.get(session_id)
    assert _assistant_count(session) <= settings.max_turns


def test_reply_rejects_empty_answer(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    with pytest.raises(InvalidInput):
        decide_and_advance(session_id, "   ")


def test_reply_unknown_session_raises():
    with pytest.raises(SessionNotFound):
        decide_and_advance("does-not-exist", "a valid non-empty answer")


def test_stream_reply_question_yields_token_then_done_events(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    decide_and_advance(session_id, "an answer")

    events = [
        json.loads(e.removeprefix("data: ").strip())
        for e in stream_reply_question(session_id)
    ]

    token_events = [e for e in events if e["type"] == "token"]
    assert token_events
    assert "".join(e["text"] for e in token_events)

    assert events[-1]["type"] == "done"
    assert "session_cost" in events[-1]


def test_stream_reply_question_unknown_session_raises():
    with pytest.raises(SessionNotFound):
        list(stream_reply_question("does-not-exist"))


def test_finish_interview_returns_scorecard(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    _answer(session_id, "A reasonable answer about the topic.")

    scorecard = finish_interview(session_id)

    assert isinstance(scorecard, Scorecard)
    assert 5 <= len(scorecard.topic_scores) <= 6
    assert scorecard.overall_assessment
    assert len(scorecard.strengths) >= 2
    assert len(scorecard.gaps) >= 2
    assert scorecard.focus_recommendation


def test_finish_interview_unknown_session_raises():
    with pytest.raises(SessionNotFound):
        finish_interview("does-not-exist")


def test_finish_interview_with_no_answers_raises(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    with pytest.raises(InvalidInput):
        finish_interview(session_id)


def test_accumulate_usage_updates_session_totals(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    session = session_store.get(session_id)
    before_prompt = session.total_prompt_tokens

    _accumulate_usage(session, Usage(prompt_tokens=100, completion_tokens=50))

    assert session.total_prompt_tokens == before_prompt + 100
    assert session.total_completion_tokens == 50


def test_get_session_cost_reflects_accumulated_usage(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    session = session_store.get(session_id)
    _accumulate_usage(session, Usage(prompt_tokens=100, completion_tokens=50))
    session_store.save(session)

    cost = get_session_cost(session_id)

    assert cost.prompt_tokens == 100
    assert cost.completion_tokens == 50
    assert cost.turns == 1  # only the opening question so far
    assert cost.is_stub is True
    assert cost.cost_usd == 0.0  # stub pricing is zero regardless of token count


def test_judge_messages_only_show_covered_topics(valid_cv, valid_jd):
    session_id, _ = _start_and_ask(valid_cv, valid_jd)
    _answer(session_id, "first answer")  # stub follows up; stays on topic 0
    session = session_store.get(session_id)

    system = _build_judge_messages(session)[0]["content"]

    covered = session.interview_plan.topics[: session.current_topic_index + 1]
    uncovered = session.interview_plan.topics[session.current_topic_index + 1 :]
    assert uncovered  # sanity check: there really are unreached topics here

    for topic in covered:
        assert topic.title in system
    for topic in uncovered:
        assert topic.title not in system
