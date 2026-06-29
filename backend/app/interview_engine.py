from uuid import uuid4

from app.config import settings
from app.input_guard import validate_inputs, wrap_untrusted
from app.llm import get_llm_client
from app.prompts import (
    CLASSIFIER_SYSTEM_PROMPT,
    CV_TAG,
    INTERVIEW_PLAN_SYSTEM_PROMPT,
    INTERVIEWER_SYSTEM_PROMPT,
    JD_TAG,
)
from app.schemas import (
    Classification,
    InterviewPlan,
    Message,
    MessageRole,
    Session,
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
    # Get the forst question from the topic context
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
