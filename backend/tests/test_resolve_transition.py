import pytest

from app.interview_engine import Transition, resolve_transition
from app.schemas import InterviewerAction

A = InterviewerAction

@pytest.mark.parametrize(
    "proposed,followups,idx,num_topics,questions_asked,expected",
    [
        (A.advance, 0, 0, 6, 12, Transition.finish),      # turn cap reached
        (A.follow_up, 0, 0, 6, 3, Transition.follow_up),  # budget free -> probe
        (A.follow_up, 1, 0, 6, 3, Transition.advance),    # budget used -> advance
        (A.advance, 0, 2, 6, 3, Transition.advance),      # mid-interview advance
        (A.advance, 1, 5, 6, 8, Transition.finish),       # advance off last topic
        (A.follow_up, 0, 5, 6, 8, Transition.follow_up),  # last topic still probes
    ],
)
def test_resolve_transition(
    proposed, followups, idx, num_topics, questions_asked, expected
):
    assert (
        resolve_transition(
            proposed,
            followups,
            idx,
            num_topics,
            questions_asked,
            max_turns=12,
            max_followups=1,
        )
        == expected
    )
