# stdlib

# third party
from langchain_anthropic import ChatAnthropic

# first party
from dbt_assistant.llm_providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    def __init__(self, model: str, temperature: float, max_tokens: int, **kwargs):
        super().__init__(model, temperature, max_tokens, **kwargs)

    def get_llm_model(self):
        return ChatAnthropic(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_tokens_to_sample=4096,
            api_key=self.api_key,
            **self.kwargs,
        )
