from enum import Enum
from uuid import uuid4

from app.config import settings
from app.input_guard import(
    validate_inputs,
    wrap_untrusted, 
    validate_answer)
from app.llm import get_llm_client
from app.prompts import (
    CANDIDATE_ANSWER_TAG,
    CLASSIFIER_SYSTEM_PROMPT,
    CV_TAG,
    INTERVIEW_PLAN_SYSTEM_PROMPT,
    INTERVIEWER_SYSTEM_PROMPT,
    INTERVIEWER_TURN_SYSTEM_PROMPT,
    JD_TAG,
)
from app.schemas import (
    Classification,
    InterviewerAction,
    InterviewPlan,
    Message,
    MessageRole,
    Session,
    InterviewerTurn
)
from app.session_store import session_store


def _messages(system: str, user: str) -> list[dict]:
    """Assemble a system + user message pair for an LLM call."""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def start_interview(cv_text: str, jd_text: str) -> tuple[str, str]:
    """Validate inputs, classify + plan the interview, produce the first
    question, persist the session, and return (session_id, first_question)."""
    jd = validate_inputs(cv_text, jd_text)
    client = get_llm_client()

    classification = client.complete(
        _messages(CLASSIFIER_SYSTEM_PROMPT, wrap_untrusted(JD_TAG, jd)),
        temperature=settings.temp_classifier,
        response_schema=Classification,
    ).parsed

    plan_data = f"{wrap_untrusted(JD_TAG, jd)}\n\n{wrap_untrusted(CV_TAG, cv_text)}"
    plan = client.complete(
        _messages(INTERVIEW_PLAN_SYSTEM_PROMPT, plan_data),
        temperature=settings.temp_planner,
        response_schema=InterviewPlan,
    ).parsed

    first_topic = plan.topics[0]
    # implement the classified roles and 
    interviewer_system = INTERVIEWER_SYSTEM_PROMPT.format(
        interview_type=classification.interview_type.value,
        seniority=classification.seniority.value,
    )

    topic_context = f"Topic: {first_topic.title}\nFocus: {first_topic.focus}"
    first_question = client.complete(
        _messages(interviewer_system, topic_context),
        temperature=settings.temp_interviewer,
        response_schema=None,
    ).content

    session = Session(
        session_id=str(uuid4()),
        classification=classification,
        interview_plan=plan,
        transcript=[Message(role=MessageRole.assistant, content=first_question)],
    )
    session_store.save(session)

    return session.session_id, first_question

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
    if questions_asked >= max_turns:
        return Transition.finish
    
    if (proposed_action == InterviewerAction.follow_up
     and followups_asked < max_followups):
        return Transition.follow_up

    if current_topic_index < num_topics - 1:
        return Transition.advance
    
    return Transition.finish

def _build_interviewer_messages(session: Session) -> list[dict]:
    topics = session.interview_plan.topics
    current = topics[session.current_topic_index]
    follow_up_allowed = session.followups_asked < settings.max_followups_per_topic
    has_next = session.current_topic_index + 1 < len(topics)

    system = INTERVIEWER_TURN_SYSTEM_PROMPT.format(
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

def reply(session_id: str, answer: str) -> tuple[bool, str | None]:
    cleaned_answer = validate_answer(answer) 
    session = session_store.get(session_id)

    session.transcript.append(Message(role=MessageRole.user, content=cleaned_answer))

    turn = get_llm_client().complete(
        _build_interviewer_messages(session),
        temperature=settings.temp_interviewer,
        response_schema=InterviewerTurn,
    ).parsed

    questions_asked = sum(
        1 for m in session.transcript if m.role == MessageRole.assistant
    )
    outcome = resolve_transition(
        turn.action, session.followups_asked, session.current_topic_index,
        len(session.interview_plan.topics), questions_asked,
        settings.max_turns, settings.max_followups_per_topic,
    )

    if outcome == Transition.finish:
        session_store.save(session)
        return True, None

    if outcome == Transition.follow_up:
        session.followups_asked += 1
    else:  # advance to the next topic
        session.current_topic_index += 1
        session.followups_asked = 0

    session.transcript.append(
        Message(role=MessageRole.assistant, content=turn.question)
    )
    session_store.save(session)
    return False, turn.question


