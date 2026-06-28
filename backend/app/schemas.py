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
        description="Short label naming the area to cover, e.g. 'System design'.",
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
