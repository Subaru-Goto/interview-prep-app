import pytest

from app.config import settings
from app.input_guard import InvalidInput
from app.interview_engine import (
    _build_interviewer_messages,
    _build_judge_messages,
    finish_interview,
    reply,
    start_interview,
)
from app.prompts import JUDGE_ANTI_INJECTION_GUARD, STAY_ON_TASK_GUARD
from app.schemas import MessageRole, Scorecard, Session
from app.session_store import SessionNotFound, session_store


def test_start_interview_returns_session_and_question(valid_cv, valid_jd):
    session_id, question = start_interview(valid_cv, valid_jd)
    assert isinstance(session_id, str) and session_id
    assert isinstance(question, str) and question


def test_start_interview_persists_session(valid_cv, valid_jd):
    session_id, _ = start_interview(valid_cv, valid_jd)
    session = session_store.get(session_id)
    assert isinstance(session, Session)
    assert session.classification is not None
    assert 5 <= len(session.interview_plan.topics) <= 6
    assert session.transcript[0].role == MessageRole.assistant


def test_plan_is_server_side_only(valid_cv, valid_jd):
    session_id, question = start_interview(valid_cv, valid_jd)
    stored = session_store.get(session_id)
    assert len(stored.interview_plan.topics) >= 5
    assert all(isinstance(value, str) for value in (session_id, question))


def test_start_interview_rejects_invalid_input(valid_jd):
    with pytest.raises(InvalidInput):
        start_interview("", valid_jd)

def _assistant_count(session):
    return sum(1 for m in session.transcript if m.role == MessageRole.assistant)


def test_reply_returns_next_question_and_appends(valid_cv, valid_jd):
    session_id, _ = start_interview(valid_cv, valid_jd)
    before = len(session_store.get(session_id).transcript)

    done, question = reply(session_id, "A reasonable answer about the topic.")

    assert done is False
    assert isinstance(question, str) and question
    transcript = session_store.get(session_id).transcript
    # one candidate answer + one new question appended
    assert len(transcript) == before + 2
    assert transcript[-2].role == MessageRole.user
    assert transcript[-1].role == MessageRole.assistant


def test_reply_enforces_one_followup_then_advances(valid_cv, valid_jd):
    # the stub always proposes follow_up, so the engine's limit is what advances
    session_id, _ = start_interview(valid_cv, valid_jd)

    reply(session_id, "first answer")
    session = session_store.get(session_id)
    assert session.followups_asked == 1     # probed the current topic
    assert session.current_topic_index == 0  # stayed on the same topic

    reply(session_id, "second answer")
    session = session_store.get(session_id)
    assert session.current_topic_index == 1  # engine forced the advance
    assert session.followups_asked == 0      # counter reset on advance


def test_interviewer_prompt_includes_stay_on_task_guard(valid_cv, valid_jd):
    session_id, _ = start_interview(valid_cv, valid_jd)
    session = session_store.get(session_id)

    system = _build_interviewer_messages(session)[0]["content"]

    assert STAY_ON_TASK_GUARD in system


def test_judge_prompt_includes_anti_injection_guard(valid_cv, valid_jd):
    session_id, _ = start_interview(valid_cv, valid_jd)
    reply(session_id, "first answer")
    session = session_store.get(session_id)

    system = _build_judge_messages(session)[0]["content"]

    assert JUDGE_ANTI_INJECTION_GUARD in system


def test_reply_is_bounded_and_finishes(valid_cv, valid_jd):
    session_id, _ = start_interview(valid_cv, valid_jd)

    done = False
    for _ in range(50):  # safety bound; should finish well before this
        done, _ = reply(session_id, "an answer")
        if done:
            break

    assert done is True
    session = session_store.get(session_id)
    assert _assistant_count(session) <= settings.max_turns


def test_reply_rejects_empty_answer(valid_cv, valid_jd):
    session_id, _ = start_interview(valid_cv, valid_jd)
    with pytest.raises(InvalidInput):
        reply(session_id, "   ")


def test_reply_unknown_session_raises():
    with pytest.raises(SessionNotFound):
        reply("does-not-exist", "a valid non-empty answer")


def test_finish_interview_returns_scorecard(valid_cv, valid_jd):
    session_id, _ = start_interview(valid_cv, valid_jd)
    reply(session_id, "A reasonable answer about the topic.")

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
    session_id, _ = start_interview(valid_cv, valid_jd)
    with pytest.raises(InvalidInput):
        finish_interview(session_id)


def test_judge_messages_only_show_covered_topics(valid_cv, valid_jd):
    session_id, _ = start_interview(valid_cv, valid_jd)
    reply(session_id, "first answer")  # stub follows up; stays on topic 0
    session = session_store.get(session_id)

    system = _build_judge_messages(session)[0]["content"]

    covered = session.interview_plan.topics[: session.current_topic_index + 1]
    uncovered = session.interview_plan.topics[session.current_topic_index + 1 :]
    assert uncovered  # sanity check: there really are unreached topics here

    for topic in covered:
        assert topic.title in system
    for topic in uncovered:
        assert topic.title not in system
