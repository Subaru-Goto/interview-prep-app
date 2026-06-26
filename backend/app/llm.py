from abc import ABC, abstractmethod
from app.config import settings
from pydantic import BaseModel
from openai import OpenAI
from functools import lru_cache

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0

class CompletionResult(BaseModel):
    content: str | None
    usage: Usage

class LLMClient(ABC):                       # the "socket" — the contract
    @abstractmethod
    def complete(
        self, 
        messages: list[dict], 
        temperature: float = 0.7
        ) -> CompletionResult:
        
        pass


class FakeLLMClient(LLMClient):             # ← now inherits the contract
    def complete(
        self, 
        messages: list[dict], 
        temperature: float = 0.7
        ) -> CompletionResult:
        last_message = messages[-1]["content"]
        return CompletionResult(
            content=f"[FAKE LLM] You said: {last_message}",
            usage=Usage(
                prompt_tokens=0,
                completion_tokens=0,
            ),
        )

class OpenRouterLLMClient(LLMClient):
    def __init__(self):
        self.base_url = settings.openrouter_base_url
        self.api_key = settings.openrouter_api_key
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def complete(
        self,
        messages: list[dict],
        temperature: float = 0.7
        ) -> CompletionResult:
        response = self.client.chat.completions.create(
            model=settings.model,
            messages=messages,
            temperature=temperature
        )
        return CompletionResult(
            content=response.choices[0].message.content,
            usage=Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            ),
        )

# Cache the LLM client
@lru_cache
def get_llm_client() -> LLMClient:
    if settings.use_fake_llm:
        return FakeLLMClient()
    return OpenRouterLLMClient()