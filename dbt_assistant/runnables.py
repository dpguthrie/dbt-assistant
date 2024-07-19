# first party
from dbt_assistant import prompts as dbt_prompts
from dbt_assistant import tools as dbt_tools
from dbt_assistant.llm import LLMFactory
from dbt_assistant.tools.pydantic import CompleteOrEscalate

llm = LLMFactory.create_llm()


admin_api_runnable = dbt_prompts.admin_api_assistant_prompt | llm.bind_tools(
    dbt_tools.admin_api_tools + [CompleteOrEscalate]
)
discovery_api_runnable = dbt_prompts.discovery_api_assistant_prompt | llm.bind_tools(
    dbt_tools.discovery_api_tools + [CompleteOrEscalate]
)
docs_runnable = dbt_prompts.docs_assistant_prompt | llm.bind_tools(
    [dbt_tools.docs_tool] + [CompleteOrEscalate]
)
hub_runnable = dbt_prompts.hub_assistant_prompt | llm.bind_tools(
    [dbt_tools.dbt_hub_retriever_tool] + [CompleteOrEscalate]
)
primary_assistant_runnable = dbt_prompts.primary_assistant_prompt | llm.bind_tools(
    dbt_tools.primary_assistant_tools + [CompleteOrEscalate]
)
semantic_layer_runnable = dbt_prompts.semantic_layer_assistant_prompt | llm.bind_tools(
    dbt_tools.semantic_layer_tools + [CompleteOrEscalate]
)

__all__ = [
    "admin_api_runnable",
    "discovery_api_runnable",
    "docs_runnable",
    "hub_runnable",
    "primary_assistant_runnable",
    "semantic_layer_runnable",
]
