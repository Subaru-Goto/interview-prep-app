import pytest
from pydantic import ValidationError

from app.schemas import (
    Classification,
    InterviewPlan,
    InterviewTopic,
    Scorecard,
    TopicScore,
)

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


def make_topic_scores(n: int) -> list[TopicScore]:
    return [
        TopicScore(topic_title=f"Topic {i}", topic_score=3, feedback=f"Feedback {i}")
        for i in range(n)
    ]


def make_scorecard(n_topics=5, n_strengths=2, n_gaps=2) -> Scorecard:
    return Scorecard(
        topic_scores=make_topic_scores(n_topics),
        overall_assessment="Solid overall performance with room to grow.",
        strengths=[f"Strength {i}" for i in range(n_strengths)],
        gaps=[f"Gap {i}" for i in range(n_gaps)],
        focus_recommendation="Practice structuring answers more concisely.",
    )


def test_scorecard_with_five_topic_scores_is_valid():
    assert len(make_scorecard(n_topics=5).topic_scores) == 5


def test_scorecard_with_six_topic_scores_is_valid():
    assert len(make_scorecard(n_topics=6).topic_scores) == 6


def test_scorecard_with_one_topic_score_is_valid():
    # an early-ended interview may only have covered one topic
    assert len(make_scorecard(n_topics=1).topic_scores) == 1


def test_scorecard_with_no_topic_scores_rejected():
    with pytest.raises(ValidationError):
        make_scorecard(n_topics=0)


def test_too_many_topic_scores_rejected():
    with pytest.raises(ValidationError):
        make_scorecard(n_topics=7)


def test_too_few_strengths_rejected():
    with pytest.raises(ValidationError):
        make_scorecard(n_strengths=1)


def test_too_few_gaps_rejected():
    with pytest.raises(ValidationError):
        make_scorecard(n_gaps=1)


def test_topic_score_above_range_rejected():
    with pytest.raises(ValidationError):
        TopicScore(topic_title="Topic", topic_score=6, feedback="feedback")


def test_topic_score_below_range_rejected():
    with pytest.raises(ValidationError):
        TopicScore(topic_title="Topic", topic_score=0, feedback="feedback")
