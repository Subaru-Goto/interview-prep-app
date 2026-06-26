from abc import ABC, abstractmethod
from app.config import settings

class LLMClient(ABC):                       # the "socket" — the contract
    @abstractmethod
    def complete(self, messages: list[dict]) -> str:
        """Every LLM client must turn a messages list into a reply string."""
        pass


class FakeLLMClient(LLMClient):             # ← now inherits the contract
    def complete(self, messages: list[dict]) -> str:
        last_message = messages[-1]["content"]
        return f"[FAKE LLM] You said: {last_message}"


def get_llm_client() -> LLMClient:
    if settings.use_fake_llm:
        return FakeLLMClient()
    else:
        raise NotImplementedError("Real OpenRouter client arrives in issue 002")
