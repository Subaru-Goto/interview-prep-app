import pytest
from pydantic import ValidationError

from app.schemas import Classification, InterviewPlan, InterviewTopic

VALID_REASONING = "Candidate is strong in backend but the JD stresses scale."


def make_topics(n: int) -> list[InterviewTopic]:
    return [
        InterviewTopic(title=f"Topic {i}", focus=f"probe area {i}")
        for i in range(n)
    ]


def make_plan(n: int) -> InterviewPlan:
    return InterviewPlan(reasoning=VALID_REASONING, topics=make_topics(n))


def test_plan_with_five_topics_is_valid():
    plan = make_plan(5)
    assert len(plan.topics) == 5


def test_plan_with_six_topics_is_valid():
    plan = make_plan(6)
    assert len(plan.topics) == 6


def test_valid_classification():
    c = Classification(interview_type="technical_analytical", seniority="junior")
    assert c.interview_type == "technical_analytical"
    assert c.seniority == "junior"


def test_too_few_topics_rejected():
    with pytest.raises(ValidationError):
        make_plan(4)


def test_too_many_topics_rejected():
    with pytest.raises(ValidationError):
        make_plan(7)


def test_empty_topic_title_rejected():
    with pytest.raises(ValidationError):
        InterviewTopic(title="", focus="something")


def test_invalid_interview_type_rejected():
    with pytest.raises(ValidationError):
        Classification(interview_type="banana", seniority="junior")


def test_invalid_seniority_rejected():
    with pytest.raises(ValidationError):
        Classification(interview_type="technical_analytical", seniority="lead")
