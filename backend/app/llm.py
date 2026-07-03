from abc import ABC, abstractmethod
from functools import lru_cache

from openai import OpenAI
from pydantic import BaseModel

from app.config import ReasoningEffort, settings
from app.schemas import (
    Classification,
    InterviewerAction,
    InterviewerTurn,
    InterviewPlan,
    InterviewTopic,
    InterviewType,
    Scorecard,
    Seniority,
    TopicScore,
)


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0


class CompletionResult(BaseModel):
    content: str | None = None
    # Parsed can be Classification, InterviewPlan, InterviewerTurn, Scorecard, or None
    parsed: BaseModel | None = None
    usage: Usage


class LLMClient(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[dict],
        reasoning_effort: ReasoningEffort = ReasoningEffort.medium,
        response_schema: type[BaseModel] | None = None,
    ) -> CompletionResult: ...


class FakeLLMClient(LLMClient):
    def complete(
        self,
        messages: list[dict],
        reasoning_effort: ReasoningEffort = ReasoningEffort.medium,
        response_schema: type[BaseModel] | None = None,
    ) -> CompletionResult:
        usage = Usage()

        if response_schema is None:
            last_message = messages[-1]["content"]
            return CompletionResult(
                content=f"[FAKE LLM] You said: {last_message}",
                usage=usage,
            )

        if response_schema is Classification:
            fake = Classification(
                interview_type=InterviewType.technical_analytical,
                seniority=Seniority.mid,
            )
            return CompletionResult(parsed=fake, usage=usage)

        if response_schema is InterviewPlan:
            fake = InterviewPlan(
                reasoning="Fake reasoning for development.",
                topics=[
                    InterviewTopic(title=f"Topic {i}", focus=f"Probe area {i}")
                    for i in range(5)
                ],
            )
            return CompletionResult(parsed=fake, usage=usage)

        if response_schema is InterviewerTurn:
            fake = InterviewerTurn(
                reasoning="Fake reasoning for development.",
                action=InterviewerAction.follow_up,
                question="[FAKE LLM] Fake question",
            )
            return CompletionResult(parsed=fake, usage=usage)

        if response_schema is Scorecard:
            fake = Scorecard(
                overall_assessment="Fake assessment for development.",
                topic_scores=[
                    TopicScore(
                        topic_title=f"Topic {i}",
                        topic_score=i + 1,
                        feedback=f"Feedback {i}",
                    )
                    for i in range(5)
                ],
                strengths=["Strength 1", "Strength 2"],
                gaps=["Gap 1", "Gap 2"],
                focus_recommendation="Focus on gaps.",
            )
            return CompletionResult(parsed=fake, usage=usage)

        raise ValueError(f"No canned fake response for {response_schema.__name__}")


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
        reasoning_effort: ReasoningEffort = ReasoningEffort.medium,
        response_schema: type[BaseModel] | None = None,
    ) -> CompletionResult:
        # `reasoning` is an OpenRouter-specific field the OpenAI SDK doesn't
        # model natively, so it's passed through via extra_body.
        extra_body = {"reasoning": {"effort": reasoning_effort.value}}

        if response_schema is None:
            response = self.client.chat.completions.create(
                model=settings.model, messages=messages, extra_body=extra_body
            )
        else:
            response = self.client.chat.completions.parse(
                model=settings.model,
                messages=messages,
                response_format=response_schema,
                extra_body=extra_body,
            )

        usage = Usage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            cost=getattr(response.usage, "cost", None) or 0.0,
        )
        message = response.choices[0].message

        if response_schema is None:
            return CompletionResult(content=message.content, usage=usage)
        return CompletionResult(parsed=message.parsed, usage=usage)


# Cache the LLM client
@lru_cache
def get_llm_client() -> LLMClient:
    if settings.use_fake_llm:
        return FakeLLMClient()
    return OpenRouterLLMClient()
