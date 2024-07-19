# stdlib
import os

# third party
from langchain_openai import ChatOpenAI

# first party
from dbt_assistant.llm_providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, model: str, temperature: float, max_tokens: int, **kwargs):
        self.base_url = os.getenv("OPENAI_BASE_URL", None)
        super().__init__(model, temperature, max_tokens, **kwargs)

    def get_llm_model(self):
        llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
            **self.kwargs,
        )
        if self.base_url:
            llm.openai_api_base = self.base_url

        return llm
