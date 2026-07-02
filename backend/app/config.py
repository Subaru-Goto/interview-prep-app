from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum

class Model(str, Enum):
    GPT_5_4_nano = "openai/gpt-5.4-nano"
    GPT_5_nano = "openai/gpt-5-nano"

class PromptTechnique(str, Enum):
    "This is to select a type of prompt engineering technique"
    zero_shot="zero_shot"
    few_shot="few_shot"
    role_play="role_play"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    use_fake_llm: bool = False
    model: Model = Model.GPT_5_nano
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    temp_classifier: float = 0.1
    temp_planner: float = 0.4
    temp_interviewer: float = 0.6
    temp_judge: float = 0.0
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
    prompt_technique:PromptTechnique=PromptTechnique.few_shot
    
settings = Settings()
