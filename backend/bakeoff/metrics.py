from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from app.config import settings
from bakeoff.openrouter_model import OpenRouterModel

evaluator = OpenRouterModel(
    model_name=settings.model,
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
)

question_evaluator = GEval(
    name="SingleFocusedQuestion",
    criteria=(
        "Determine whether 'actual_output' is a single, focused interview "
        "question relevant to the topic described in 'input', answerable "
        "in a few minutes. "
        "Penalize outputs that bundle multiple sub-questions together, ask "
        "about several unrelated things at once, use enumerated lists "
        "(e.g. '1) ... 2) ... 3) ...'), or join separate questions with "
        "words like 'also', 'additionally', or 'and'. "
        "A good output asks exactly one clear thing and nothing else."
        "It is also easier for candidates to answer"
    ),
    evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
    model=evaluator,
    threshold=0.7,
)

if __name__ == "__main__":
    bad_case = """
    Can you walk me through how you would own cross-domain hardware productization
    (mechanical, electronics, firmware, fluidics, enclosures, interfaces) from MVP
    to a field-ready system. Outline your plan for transitioning to production,
    including milestones, DFx activities, risk management, and decision criteria
    that balance performance, reliability, cost, and manufacturability. If helpful,
    ground it with a hypothetical device and walk through key trade-offs and handoffs
    to manufacturing and field support.
    """.strip()

    bad_test_case = LLMTestCase(
        input=(
            "Topic: Hardware productization — Focus: taking a device from "
            "MVP to a field-ready system."
        ),
        actual_output=bad_case,
    )
    question_evaluator.measure(bad_test_case)
    print(question_evaluator.score, question_evaluator.reason)
