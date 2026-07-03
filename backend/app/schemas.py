from enum import Enum

from pydantic import BaseModel, Field


class InterviewType(str, Enum):
    technical_analytical = "technical_analytical"
    behavioral_judgment = "behavioral_judgment"


class Seniority(str, Enum):
    """Change how deep agent asks questions"""

    junior = "junior"
    mid = "mid"
    senior = "senior"

class Classification(BaseModel):
    interview_type: InterviewType = Field(
        description=(
            "Interview format inferred from the job description: "
            "'technical_analytical' for problem-solving / analytical roles such "
            "as Tech/Engineering, Data, Consulting & Strategy, "
            "Finance/Accounting, Product, Science, 'behavioral_judgment' for "
            "situational-judgment roles such as HR/People, Management, "
            "Admin, Sales, Marketing, Education."
        )
    )
    seniority: Seniority = Field(
        description=(
            "Target level inferred from the job description — from required years "
            "of experience, role scope, and leadership/ownership signals. Map "
            "lead/staff/principal/manager to senior; entry/associate/intern/"
            "graduate to junior; everything else to mid. Tunes how deep and "
            "demanding the questions are."
        )
    )


class InterviewTopic(BaseModel):
    title: str = Field(
        min_length=1,
        description=(
            "Short label naming the area to cover, e.g. 'System design', "
            "'business cases', 'statistics', 'A/B testing'."
        ),
    )
    focus: str = Field(
        min_length=1,
        description=(
            "Specific angle to probe for this topic: what to explore to test "
            "how well the candidate's background (from the CV) fits what the "
            "role requires (from the job description). Not a restatement of "
            "the title."
        ),
    )


class InterviewPlan(BaseModel):
    reasoning: str = Field(
        min_length=1,
        description=(
            "Step-by-step analysis written BEFORE the topics: the candidate's "
            "strengths and gaps from the CV, what the job description most "
            "needs to verify, and why these topics were chosen. Think here "
            "first, then list topics."
        ),
    )
    topics: list[InterviewTopic] = Field(
        min_length=5,
        max_length=6,
        description="Ordered list of 5-6 topics the interview will cover.",
    )


class MessageRole(str, Enum):
    """Role of the speaker in the interview."""

    assistant = "assistant"
    user = "user"


class Message(BaseModel):
    role: MessageRole = Field(description="Role of the speaker in the interview.")
    content: str = Field(min_length=1, description="Content of the message")


class Session(BaseModel):
    session_id: str = Field(
        min_length=1, description="Unique identifier for the session."
    )
    classification: Classification
    interview_plan: InterviewPlan
    transcript: list[Message] = Field(
        min_length=1,
        description="Ordered list of messages exchanged during the interview.",
    )
    current_topic_index: int = Field(
        default=0, description="Index of the current topic in the interview plan."
    )
    followups_asked: int = Field(
        default=0,
        description="Number of follow-up questions asked during the interview.",
    )
    total_prompt_tokens: int = Field(
        default=0, description="Prompt tokens used across every LLM call so far."
    )
    total_completion_tokens: int = Field(
        default=0, description="Completion tokens used across every LLM call so far."
    )
    total_cost_usd: float = Field(
        default=0.0, description="Accumulated USD cost across every LLM call so far."
    )


class SessionCost(BaseModel):
    """Operator-facing cost summary for a session, returned on every call."""

    turns: int = Field(
        ge=0, description="Number of interviewer questions asked so far."
    )
    prompt_tokens: int = Field(ge=0, description="Total prompt tokens used so far.")
    completion_tokens: int = Field(
        ge=0, description="Total completion tokens used so far."
    )
    cost_usd: float = Field(ge=0.0, description="Accumulated cost in USD so far.")
    is_stub: bool = Field(
        description=(
            "True when running against the fake LLM, so cost_usd is a "
            "placeholder zero rather than a real charge."
        )
    )


class InterviewerAction(str, Enum):
    """Interviewer's next action"""

    follow_up = "follow_up"
    advance = "advance"


class InterviewerTurn(BaseModel):
    reasoning: str = Field(
        min_length=1,
        description=(
            "Analyze the candidate's most recent answer before deciding: "
            "was it complete, vague, or notably strong, and is the current "
            "topic sufficiently covered? Think here first, then choose the "
            "action. Do ALL of your step-by-step thinking in this field — "
            "none of it belongs in 'question'."
        ),
    )
    action: InterviewerAction = Field(
        description=(
            "Choose follow_up when the answer is vague, incomplete, or notably "
            "strong and worth probing further on this topic; choose advance "
            "when the topic is sufficiently covered."
        )
    )
    question: str = Field(
        min_length=1,
        description=(
            "Exactly one interview question: a single sentence ending in "
            "exactly one question mark, asking about exactly one thing. "
            "No numbered or bulleted lists. Watch specifically for the word "
            "'and': 'How did you do X and Y?' is TWO questions disguised as "
            "one sentence, not one question — this is the single most common "
            "mistake, avoid it above all else. Same for 'also' and "
            "'additionally'. If your draft question connects two different "
            "things with one of those words, delete everything after the "
            "connector and keep only the single most important thing."
        ),
    )

class TopicScore(BaseModel):
    topic_title: str = Field(min_length=1, description="The title of the scored topic.")
    topic_score: int = Field(
        ge=1,
        le=5,
        description=(
            "1 to 5 likert scale, anchored so each point means the same "
            "thing across every candidate: "
            "1 - no relevant content, unable to answer, or entirely off-topic; "
            "2 - attempted the topic but mostly incorrect, vague, or missing "
            "key parts; "
            "3 - correct on the fundamentals but shallow, with noticeable gaps; "
            "4 - solid and mostly complete, with only minor gaps; "
            "5 - complete, accurate, and well-reasoned, with no meaningful gaps. "
            "Score based only on the correctness, depth, and relevance of the "
            "content — a concise, correct answer should score as well as a "
            "longer one covering the same ground. Do not let length, "
            "elaboration, or confident tone raise the score on their own."
        ),
    )
    feedback: str = Field(
        min_length=1,
        description=(
            "Simple and direct max 1-2 sentences about the candidate's "
            "performance on this topic."
        ),
    )


class Scorecard(BaseModel):
    topic_scores: list[TopicScore] = Field(
        min_length=1,
        max_length=6,
        description=(
            "One entry per topic that was actually discussed in the transcript "
            "— never invent a score for a topic with no evidence there. If the "
            "interview ended early, this list will have fewer than the total "
            "planned topics; that is expected."
        ),
    )
    overall_assessment: str = Field(
        min_length=1,
        description=(
            "A short synthesis (2-4 sentences) of the candidate's performance "
            "across the topics actually covered, written after reviewing the "
            "per-topic scores. If the interview ended before covering every "
            "planned topic, say so explicitly (e.g. how many of the planned "
            "topics were reached)."
        ),
    )
    strengths: list[str] = Field(
        min_length=2,
        max_length=4,
        description="2-4 concrete strengths observed during the interview.",
    )
    gaps: list[str] = Field(
        min_length=2,
        max_length=4,
        description="2-4 concrete gaps or areas of concern from the interview.",
    )
    focus_recommendation: str = Field(
        min_length=1,
        description=(
            "2-4 sentences of coaching guidance: what the candidate should "
            "practice or focus on next, prioritized by the gaps above."
        ),
    )
