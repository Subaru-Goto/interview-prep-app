from deepeval.test_case import LLMTestCase

from app.config import PromptTechnique, settings
from app.interview_engine import _build_interviewer_messages
from app.llm import get_llm_client
from app.schemas import (
    Classification,
    InterviewerTurn,
    InterviewPlan,
    InterviewTopic,
    InterviewType,
    Message,
    MessageRole,
    Seniority,
    Session,
)
from bakeoff.metrics import question_evaluator

FIXTURE_TOPIC_INPUT = (
    "Topic: System design — Focus: How they'd design a service that scales "
    "under load."
)

FIXTURE_SESSION = Session(
    session_id="bakeoff-fixture",
    classification=Classification(
        interview_type=InterviewType.technical_analytical,
        seniority=Seniority.senior,
    ),
    interview_plan=InterviewPlan(
        reasoning="Fixture plan for the prompt bake-off.",
        topics=[
            InterviewTopic(
                title="System design",
                focus="How they'd design a service that scales under load.",
            ),
            InterviewTopic(
                title="Debugging under pressure",
                focus="How they diagnose a production incident.",
            ),

            InterviewTopic(title="API design", focus="Not used by this fixture."),
            InterviewTopic(
                title="Testing strategy", focus="Not used by this fixture."
            ),
            InterviewTopic(
                title="Team collaboration", focus="Not used by this fixture."
            ),
        ],
    ),
    transcript=[
        Message(
            role=MessageRole.assistant,
            content="Tell me about a system you designed that had to scale.",
        ),
        Message(
            role=MessageRole.user,
            content=(
                "I designed a checkout service that handled a big traffic spike "
                "during a sale. We added caching and a queue in front of the "
                "payment provider."
            ),
        ),
    ],
)


def main():
    client = get_llm_client()
    for technique in PromptTechnique:
        settings.prompt_technique = technique
        messages = _build_interviewer_messages(FIXTURE_SESSION)
        turn = client.complete(
            messages,
            temperature=settings.temp_interviewer,
            response_schema=InterviewerTurn,
        ).parsed

        test_case = LLMTestCase(
            input=FIXTURE_TOPIC_INPUT,
            actual_output=turn.question,
        )
        question_evaluator.measure(test_case)

        print(f"\n=== {technique.value} ===")
        print(f"action: {turn.action.value}")
        print(f"question: {turn.question}")
        print(f"score: {question_evaluator.score:.2f}")
        print(f"reason: {question_evaluator.reason}")


if __name__ == "__main__":
    main()
