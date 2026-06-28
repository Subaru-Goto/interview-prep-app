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
            "Specific, CV-grounded angle to probe for this topic — not a "
            "restatement of the title."
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
