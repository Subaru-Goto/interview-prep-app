from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    use_fake_llm: bool = True
    model: str = "openai/gpt-5-nano"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    temp_classifier: float = 0.1
    temp_planner: float = 0.4
    temp_interviewer: float = 0.6
    temp_judge: float = 0.0
    frontend_origin: str = "http://localhost:3000"
    min_cv_chars: int = 100
    max_cv_chars: int = 50000


settings = Settings()
