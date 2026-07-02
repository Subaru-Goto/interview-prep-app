"""
Wrapper for openrouter to use DeepEval
"""

from deepeval.models import DeepEvalBaseLLM
from openai import AsyncOpenAI, OpenAI


class OpenRouterModel(DeepEvalBaseLLM):
    def __init__(self, model_name: str, api_key: str, base_url: str):
        self.model_name = model_name
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.async_client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    def load_model(self):
        return self.client

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    async def a_generate(self, prompt: str) -> str:
        response = await self.async_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content

    def get_model_name(self) -> str:
        return self.model_name
