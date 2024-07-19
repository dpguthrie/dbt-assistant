# stdlib
import os
from typing import Any, Dict

# third party
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

DEFAULTS = {
    "temperature": 0,
    "streaming": True,
    "max_tokens": 4096,
}

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20240620"


class LLMFactory:
    @staticmethod
    def _get_llm_env_vars() -> Dict[str, Any]:
        prefix = "DBT_ASSISTANT_"
        env_vars = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                param_name = key[len(prefix) :].lower()
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass

                env_vars[param_name] = value
        for default_key, default_value in DEFAULTS.items():
            if default_key not in env_vars:
                env_vars[default_key] = default_value
        return env_vars

    @staticmethod
    def create_llm(model_name: str = None):
        env_vars = LLMFactory._get_llm_env_vars()
        if "OPENAI_API_KEY" in os.environ:
            return ChatOpenAI(
                model=model_name or env_vars.pop("model", DEFAULT_OPENAI_MODEL),
                **env_vars,
            )

        if "ANTHROPIC_API_KEY" in os.environ:
            return ChatAnthropic(
                model=model_name or env_vars.pop("model", DEFAULT_ANTHROPIC_MODEL),
                **env_vars,
            )

        raise ValueError("No valid LLM provider found.")
