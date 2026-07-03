from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Model(str, Enum):
    GPT_5_4_nano = "openai/gpt-5.4-nano"
    GPT_5_nano = "openai/gpt-5-nano"

class PromptTechnique(str, Enum):
    "This is to select a type of prompt engineering technique"
    zero_shot="zero_shot"
    few_shot="few_shot"
    role_play="role_play"

class ReasoningEffort(str, Enum):
    "OpenRouter reasoning.effort: how much internal reasoning the model spends"
    none = "none"
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    use_fake_llm: bool = False
    model: Model = Model.GPT_5_nano
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    reasoning_effort_classifier: ReasoningEffort = ReasoningEffort.low
    reasoning_effort_planner: ReasoningEffort = ReasoningEffort.medium
    # gpt-5-nano rejects reasoning.effort="none" outright ("Reasoning is
    # mandatory for this endpoint and cannot be disabled") — minimal is the
    # lowest level this model actually accepts.
    reasoning_effort_interviewer: ReasoningEffort = ReasoningEffort.minimal
    reasoning_effort_judge: ReasoningEffort = ReasoningEffort.high
    judge_seed: int = 42
    frontend_origin: str = "http://localhost:3000"
    min_cv_chars: int = 100
    max_cv_chars: int = 50000
    max_cv_bytes: int = 5 *1024 * 1024 #5MB
    # ratio of whitespace characters
    min_whitespace_ratio: float = 0.02
    # ratio of alphabetic characters
    min_alpha_ratio: float = 0.5
    min_jd_chars: int = 200
    max_jd_chars: int = 20000
    max_turns: int = 12
    max_followups_per_topic: int = 1
    max_answer_chars: int = 5000
    prompt_technique:PromptTechnique=PromptTechnique.zero_shot
    session_ttl_seconds: int = 3600  # 1h of inactivity
    max_sessions: int = 500

settings = Settings()
