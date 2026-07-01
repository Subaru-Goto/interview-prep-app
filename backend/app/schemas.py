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
            "action."
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
        description="The single next question or follow-up to ask the candidate.",
    )

class TopicScore(BaseModel):
    topic_title: str = Field(min_length=1, description="The title of the scored topic.")
    topic_score: int = Field(
        ge=1,
        le=5,
        description=(
            "1 to 5 likert scale: 1 - very weak, unable to answer or "
            "answer is off-topic; 3 - adequate, meets the bar with some "
            "gaps; 5 - very strong, thorough and well-reasoned answers."
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
