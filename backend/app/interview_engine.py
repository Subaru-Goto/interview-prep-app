import json
import logging
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from uuid import uuid4

from app.config import settings
from app.input_guard import (
    InvalidInput,
    validate_answer,
    validate_inputs,
    wrap_untrusted,
)
from app.llm import Usage, get_llm_client
from app.prompts import (
    CANDIDATE_ANSWER_TAG,
    CLASSIFIER_SYSTEM_PROMPT,
    CV_TAG,
    INTERVIEW_PLAN_SYSTEM_PROMPT,
    INTERVIEWER_PROMPT_REGISTRY,
    INTERVIEWER_SYSTEM_PROMPT,
    JD_TAG,
    JUDGE_SYSTEM_PROMPT,
    SINGLE_QUESTION_GUARD,
)
from app.schemas import (
    Classification,
    InterviewerAction,
    InterviewerDecision,
    InterviewPlan,
    Message,
    MessageRole,
    Scorecard,
    Session,
    SessionCost,
)
from app.session_store import session_store

logger = logging.getLogger(__name__)


def _accumulate_usage(session: Session, usage: Usage) -> None:
    session.total_prompt_tokens += usage.prompt_tokens
    session.total_completion_tokens += usage.completion_tokens
    session.total_cost_usd += usage.cost
    logger.info(
        "session %s: +%d prompt / +%d completion tokens, +$%.6f (running total $%.6f)",
        session.session_id,
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.cost,
        session.total_cost_usd,
    )


def get_session_cost(session_id: str) -> SessionCost:
    """Return the running token/cost totals for a session. Raises
    SessionNotFound if session_id doesn't exist (or has expired)."""
    session = session_store.get(session_id)
    turns = sum(1 for m in session.transcript if m.role == MessageRole.assistant)
    return SessionCost(
        turns=turns,
        prompt_tokens=session.total_prompt_tokens,
        completion_tokens=session.total_completion_tokens,
        cost_usd=session.total_cost_usd,
        is_stub=settings.use_fake_llm,
    )


def _messages(system: str, user: str) -> list[dict]:
    """Assemble a system + user message pair for an LLM call."""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def sse_event(event_type: str, data: dict) -> str:
    """Format one Server-Sent Events frame carrying a JSON payload."""
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


def start_interview(cv_text: str, jd_text: str) -> str:
    """Validate inputs, classify + plan the interview, and persist a session
    with an empty transcript. Returns session_id. Does not generate the
    opening question — call stream_first_question(session_id) next, so the
    frontend can move to the interview screen before that text exists."""
    jd = validate_inputs(cv_text, jd_text)
    client = get_llm_client()

    plan_data = f"{wrap_untrusted(JD_TAG, jd)}\n\n{wrap_untrusted(CV_TAG, cv_text)}"

    # Classification and plan generation don't depend on each other's output,
    # so run them concurrently on separate threads instead of back to back.
    with ThreadPoolExecutor(max_workers=2) as executor:
        classification_future = executor.submit(
            client.complete,
            _messages(CLASSIFIER_SYSTEM_PROMPT, wrap_untrusted(JD_TAG, jd)),
            reasoning_effort=settings.reasoning_effort_classifier,
            response_schema=Classification,
        )
        plan_future = executor.submit(
            client.complete,
            _messages(INTERVIEW_PLAN_SYSTEM_PROMPT, plan_data),
            reasoning_effort=settings.reasoning_effort_planner,
            response_schema=InterviewPlan,
        )
        classification_result = classification_future.result()
        plan_result = plan_future.result()

    session = Session(
        session_id=str(uuid4()),
        classification=classification_result.parsed,
        interview_plan=plan_result.parsed,
        transcript=[],
    )
    for result in (classification_result, plan_result):
        _accumulate_usage(session, result.usage)
    session_store.save(session)

    return session.session_id


def stream_first_question(session_id: str) -> Iterator[str]:
    """Stream the interview's opening question as SSE 'token' events, append
    it to the session's transcript once complete, then yield a final 'done'
    event carrying the updated session_cost. Raises SessionNotFound (before
    any streaming starts) if session_id doesn't exist."""
    session = session_store.get(session_id)
    first_topic = session.interview_plan.topics[0]
    interviewer_system = INTERVIEWER_SYSTEM_PROMPT.format(
        interview_type=session.classification.interview_type.value,
        seniority=session.classification.seniority.value,
    )
    topic_context = f"Topic: {first_topic.title}\nFocus: {first_topic.focus}"
    messages = _messages(interviewer_system, topic_context)

    full_text = ""
    try:
        for chunk, usage in get_llm_client().stream_complete(
            messages, reasoning_effort=settings.reasoning_effort_interviewer
        ):
            if usage is not None:
                _accumulate_usage(session, usage)
                continue
            full_text += chunk
            yield sse_event("token", {"text": chunk})
    except Exception:
        logger.error("Streaming the opening question failed", exc_info=True)
        yield sse_event(
            "error", {"message": "Could not generate the opening question."}
        )
        return

    session.transcript.append(Message(role=MessageRole.assistant, content=full_text))
    session_store.save(session)
    yield sse_event("done", {"session_cost": get_session_cost(session_id).model_dump()})


class Transition(str, Enum):
    follow_up = "follow_up"
    advance = "advance"
    finish = "finish"


def resolve_transition(
    proposed_action: InterviewerAction,
    followups_asked: int,
    current_topic_index: int,
    num_topics: int,
    questions_asked: int,
    max_turns: int,
    max_followups: int,
) -> Transition:
    """Decide the next state deterministically from the interviewer's
    proposed action and the session's bounds — the model proposes, this
    function enforces. Turn cap and topic list always win over the model's
    own request to keep following up."""
    if questions_asked >= max_turns:
        return Transition.finish

    if (
        proposed_action == InterviewerAction.follow_up
        and followups_asked < max_followups
    ):
        return Transition.follow_up

    if current_topic_index < num_topics - 1:
        return Transition.advance

    return Transition.finish


def _build_interviewer_messages(session: Session) -> list[dict]:
    topics = session.interview_plan.topics
    current = topics[session.current_topic_index]
    follow_up_allowed = session.followups_asked < settings.max_followups_per_topic
    has_next = session.current_topic_index + 1 < len(topics)

    system = INTERVIEWER_PROMPT_REGISTRY[settings.prompt_technique].format(
        interview_type=session.classification.interview_type.value,
        seniority=session.classification.seniority.value,
    )
    # Add the topics and focuses
    system += f"\n\nCurrent topic: {current.title} — {current.focus}"
    if has_next:
        next_topic = topics[session.current_topic_index + 1]
        system += f"\nNext topic: {next_topic.title} — {next_topic.focus}"
    # Add a conditional prompt
    if follow_up_allowed:
        system += "\nYou may ask one follow-up on the current topic, or advance."
    else:
        system += "\nYou have used your follow-up; advance to the next topic."

    messages = [{"role": "system", "content": system}]
    # Append the conversation history
    for m in session.transcript:
        content = m.content

        if m.role == MessageRole.user:
            content = wrap_untrusted(CANDIDATE_ANSWER_TAG, content)
        messages.append({"role": m.role.value, "content": content})
    return messages


def decide_and_advance(session_id: str, answer: str) -> Transition:
    """Record the candidate's answer, ask the interviewer LLM whether to
    follow up or advance (fast, structured, non-streamed), and update the
    session's topic/follow-up state accordingly. Returns the resolved
    Transition; Transition.finish means the interview is over — the caller
    should not stream a question. Otherwise, call
    stream_reply_question(session_id) next for the actual question text.
    Raises InvalidInput on an empty/invalid answer, SessionNotFound if
    session_id doesn't exist."""
    cleaned_answer = validate_answer(answer)
    session = session_store.get(session_id)

    session.transcript.append(Message(role=MessageRole.user, content=cleaned_answer))

    decision_result = get_llm_client().complete(
        _build_interviewer_messages(session),
        reasoning_effort=settings.reasoning_effort_interviewer,
        response_schema=InterviewerDecision,
    )
    decision = decision_result.parsed
    _accumulate_usage(session, decision_result.usage)

    questions_asked = sum(
        1 for m in session.transcript if m.role == MessageRole.assistant
    )
    outcome = resolve_transition(
        decision.action,
        session.followups_asked,
        session.current_topic_index,
        len(session.interview_plan.topics),
        questions_asked,
        settings.max_turns,
        settings.max_followups_per_topic,
    )

    if outcome == Transition.follow_up:
        session.followups_asked += 1
    elif outcome == Transition.advance:
        session.current_topic_index += 1
        session.followups_asked = 0

    session_store.save(session)
    return outcome


def stream_reply_question(session_id: str) -> Iterator[str]:
    """Stream the interviewer's next question as SSE 'token' events, append
    it to the transcript, then yield a final 'done' event carrying the
    updated session_cost. Only call after decide_and_advance() returns a
    non-finish Transition. Raises SessionNotFound (before any streaming
    starts) if session_id doesn't exist."""
    session = session_store.get(session_id)
    messages = _build_interviewer_messages(session)
    messages[0]["content"] += "\n\n" + SINGLE_QUESTION_GUARD

    full_text = ""
    try:
        for chunk, usage in get_llm_client().stream_complete(
            messages, reasoning_effort=settings.reasoning_effort_interviewer
        ):
            if usage is not None:
                _accumulate_usage(session, usage)
                continue
            full_text += chunk
            yield sse_event("token", {"text": chunk})
    except Exception:
        logger.error("Streaming the reply question failed", exc_info=True)
        yield sse_event("error", {"message": "Could not generate the next question."})
        return

    session.transcript.append(Message(role=MessageRole.assistant, content=full_text))
    session_store.save(session)
    yield sse_event("done", {"session_cost": get_session_cost(session_id).model_dump()})


def _build_judge_messages(session: Session) -> list[dict]:
    system = JUDGE_SYSTEM_PROMPT.format(
        interview_type=session.classification.interview_type.value,
        seniority=session.classification.seniority.value,
    )

    covered_topics = session.interview_plan.topics[: session.current_topic_index + 1]
    total_topics = len(session.interview_plan.topics)
    topics_text = "\n".join(f"- {t.title}: {t.focus}" for t in covered_topics)
    system += (
        f"\n\nThis interview was planned to cover {total_topics} topic(s). "
        f"{len(covered_topics)} of them were actually discussed:\n{topics_text}"
    )

    # Get the candidate's message and append to the system prompt
    messages = [{"role": "system", "content": system}]
    for m in session.transcript:
        content = m.content
        if m.role == MessageRole.user:
            content = wrap_untrusted(CANDIDATE_ANSWER_TAG, content)
        messages.append({"role": m.role.value, "content": content})
    return messages


def finish_interview(session_id: str) -> Scorecard:
    """Judge the transcript so far and return a scorecard. Does not delete
    the session — callers decide when cleanup happens. Raises InvalidInput
    if no answers were given yet, SessionNotFound if session_id doesn't
    exist."""
    session = session_store.get(session_id)

    if not any(m.role == MessageRole.user for m in session.transcript):
        raise InvalidInput("Answer at least one question before ending the interview.")

    judge_result = get_llm_client().complete(
        _build_judge_messages(session),
        reasoning_effort=settings.reasoning_effort_judge,
        response_schema=Scorecard,
        seed=settings.judge_seed,
    )
    _accumulate_usage(session, judge_result.usage)
    session_store.save(session)

    return judge_result.parsed
