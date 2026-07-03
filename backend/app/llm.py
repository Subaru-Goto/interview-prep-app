from abc import ABC, abstractmethod
from collections.abc import Iterator
from functools import lru_cache

from openai import OpenAI
from pydantic import BaseModel

from app.config import ReasoningEffort, settings
from app.schemas import (
    Classification,
    InterviewerAction,
    InterviewerDecision,
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
        seed: int | None = None,
    ) -> CompletionResult:
        """Run one chat completion. If response_schema is given, parse the
        reply into that Pydantic model (CompletionResult.parsed); otherwise
        return raw text (CompletionResult.content). seed is best-effort
        reproducibility, not a determinism guarantee."""
        ...

    @abstractmethod
    def stream_complete(
        self,
        messages: list[dict],
        reasoning_effort: ReasoningEffort = ReasoningEffort.medium,
    ) -> Iterator[tuple[str, Usage | None]]:
        """Stream a plain-text completion (no response_schema — structured
        output isn't streamed). Yields (text_chunk, None) for each token as
        it arrives, then a final ("", usage) item carrying the completed
        call's token/cost totals."""
        ...


class FakeLLMClient(LLMClient):
    def complete(
        self,
        messages: list[dict],
        reasoning_effort: ReasoningEffort = ReasoningEffort.medium,
        response_schema: type[BaseModel] | None = None,
        seed: int | None = None,
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

        if response_schema is InterviewerDecision:
            fake = InterviewerDecision(
                reasoning="Fake reasoning for development.",
                action=InterviewerAction.follow_up,
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

    def stream_complete(
        self,
        messages: list[dict],
        reasoning_effort: ReasoningEffort = ReasoningEffort.medium,
    ) -> Iterator[tuple[str, Usage | None]]:
        for word in "[FAKE LLM] Fake streamed question".split(" "):
            yield word + " ", None
        yield "", Usage()


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
        seed: int | None = None,
    ) -> CompletionResult:

        extra_body = {"reasoning": {"effort": reasoning_effort.value}}
        optional_kwargs = {"seed": seed} if seed is not None else {}

        if response_schema is None:
            response = self.client.chat.completions.create(
                model=settings.model,
                messages=messages,
                extra_body=extra_body,
                **optional_kwargs,
            )
        else:
            response = self.client.chat.completions.parse(
                model=settings.model,
                messages=messages,
                response_format=response_schema,
                extra_body=extra_body,
                **optional_kwargs,
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

    def stream_complete(
        self,
        messages: list[dict],
        reasoning_effort: ReasoningEffort = ReasoningEffort.medium,
    ) -> Iterator[tuple[str, Usage | None]]:
        extra_body = {"reasoning": {"effort": reasoning_effort.value}}
        stream = self.client.chat.completions.create(
            model=settings.model,
            messages=messages,
            extra_body=extra_body,
            stream=True,
            stream_options={"include_usage": True},
        )
        for chunk in stream:
            # The final chunk carries usage and has no choices.
            if chunk.usage is not None:
                yield "", Usage(
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    cost=getattr(chunk.usage, "cost", None) or 0.0,
                )
                continue
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta, None


# Cache the LLM client
@lru_cache
def get_llm_client() -> LLMClient:
    """Return the process-wide LLM client — FakeLLMClient in dev
    (use_fake_llm=True), otherwise the real OpenRouter client. Cached, so
    settings.use_fake_llm is only read on first call in a process."""
    if settings.use_fake_llm:
        return FakeLLMClient()
    return OpenRouterLLMClient()
