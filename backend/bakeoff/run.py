from dataclasses import dataclass

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


def _padded_topics(current: InterviewTopic, next_topic: InterviewTopic) -> list:
    """InterviewPlan.topics needs min_length=5; only the first two are ever
    read by _build_interviewer_messages() for these fixtures
    (current_topic_index=0), the rest just need to exist to keep the schema
    valid."""
    return [
        current,
        next_topic,
        InterviewTopic(title="Unused topic A", focus="Not used by this fixture."),
        InterviewTopic(title="Unused topic B", focus="Not used by this fixture."),
        InterviewTopic(title="Unused topic C", focus="Not used by this fixture."),
    ]


@dataclass
class Fixture:
    name: str
    topic_input: str
    session: Session


FIXTURES = [
    Fixture(
        name="senior-technical-system-design",
        topic_input=(
            "Topic: System design — Focus: How they'd design a service that "
            "scales under load."
        ),
        session=Session(
            session_id="bakeoff-fixture-1",
            classification=Classification(
                interview_type=InterviewType.technical_analytical,
                seniority=Seniority.senior,
            ),
            interview_plan=InterviewPlan(
                reasoning="Fixture plan for the prompt bake-off.",
                topics=_padded_topics(
                    InterviewTopic(
                        title="System design",
                        focus="How they'd design a service that scales under load.",
                    ),
                    InterviewTopic(
                        title="Debugging under pressure",
                        focus="How they diagnose a production incident.",
                    ),
                ),
            ),
            transcript=[
                Message(
                    role=MessageRole.assistant,
                    content="Tell me about a system you designed that had to scale.",
                ),
                Message(
                    role=MessageRole.user,
                    content=(
                        "I designed a checkout service that handled a big traffic "
                        "spike during a sale. We added caching and a queue in "
                        "front of the payment provider."
                    ),
                ),
            ],
        ),
    ),
    Fixture(
        name="junior-behavioral-conflict-resolution",
        topic_input=(
            "Topic: Conflict resolution — Focus: How they handle disagreements "
            "with teammates."
        ),
        session=Session(
            session_id="bakeoff-fixture-2",
            classification=Classification(
                interview_type=InterviewType.behavioral_judgment,
                seniority=Seniority.junior,
            ),
            interview_plan=InterviewPlan(
                reasoning="Fixture plan for the prompt bake-off.",
                topics=_padded_topics(
                    InterviewTopic(
                        title="Conflict resolution",
                        focus="How they handle disagreements with teammates.",
                    ),
                    InterviewTopic(
                        title="Prioritization",
                        focus="How they decide what to work on first.",
                    ),
                ),
            ),
            transcript=[
                Message(
                    role=MessageRole.assistant,
                    content="Tell me about a time you disagreed with a teammate.",
                ),
                Message(
                    role=MessageRole.user,
                    content=(
                        "A teammate wanted to skip writing tests to hit a deadline. "
                        "I pushed back and we agreed to write tests for the "
                        "critical path only."
                    ),
                ),
            ],
        ),
    ),
    Fixture(
        name="mid-technical-ab-testing",
        topic_input=(
            "Topic: A/B testing methodology — Focus: How they design and "
            "interpret experiments."
        ),
        session=Session(
            session_id="bakeoff-fixture-3",
            classification=Classification(
                interview_type=InterviewType.technical_analytical,
                seniority=Seniority.mid,
            ),
            interview_plan=InterviewPlan(
                reasoning="Fixture plan for the prompt bake-off.",
                topics=_padded_topics(
                    InterviewTopic(
                        title="A/B testing methodology",
                        focus="How they design and interpret experiments.",
                    ),
                    InterviewTopic(
                        title="Data quality",
                        focus="How they catch bad or misleading data.",
                    ),
                ),
            ),
            transcript=[
                Message(
                    role=MessageRole.assistant,
                    content="Walk me through an A/B test you ran.",
                ),
                Message(
                    role=MessageRole.user,
                    content=(
                        "I ran a test on a new checkout button color. It showed a "
                        "2% lift in conversion after two weeks, so we shipped it."
                    ),
                ),
            ],
        ),
    ),
]


def main():
    client = get_llm_client()
    scores: dict[PromptTechnique, list[float]] = {t: [] for t in PromptTechnique}

    for fixture in FIXTURES:
        print(f"\n{'=' * 20} fixture: {fixture.name} {'=' * 20}")
        for technique in PromptTechnique:
            settings.prompt_technique = technique
            messages = _build_interviewer_messages(fixture.session)
            turn = client.complete(
                messages,
                temperature=settings.temp_interviewer,
                response_schema=InterviewerTurn,
            ).parsed

            test_case = LLMTestCase(
                input=fixture.topic_input,
                actual_output=turn.question,
            )
            question_evaluator.measure(test_case)
            scores[technique].append(question_evaluator.score)

            print(f"\n--- {technique.value} ---")
            print(f"action: {turn.action.value}")
            print(f"question: {turn.question}")
            print(f"score: {question_evaluator.score:.2f}")
            print(f"reason: {question_evaluator.reason}")

    print(f"\n{'=' * 20} summary (average across {len(FIXTURES)} fixtures) {'=' * 20}")
    for technique, values in scores.items():
        average = sum(values) / len(values)
        print(
            f"{technique.value}: {average:.2f}  (runs: {[round(v, 2) for v in values]})"
        )


if __name__ == "__main__":
    main()
