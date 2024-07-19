# stdlib
from typing import Literal

# third party
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

# first party
from dbt_assistant import runnables as dbt_runnables
from dbt_assistant import tools as dbt_tools
from dbt_assistant.assistant import DbtAssistant
from dbt_assistant.state import State
from dbt_assistant.tools.pydantic import (
    CompleteOrEscalate,
    ToAdminApiAssistant,
    ToDbtHubAssistant,
    ToDiscoveryApiAssistant,
    ToDocsAssistant,
    ToSemanticLayerAssistant,
)
from dbt_assistant.utils.graph import create_entry_node, create_tool_node_with_fallback


def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant.

    This lets the full graph explicitly track the dialog flow and delegate control
    to specific sub-graphs.
    """
    messages = []
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }


# Each delegated workflow can directly respond to the user
# When the user responds, we want to return to the currently active workflow.
def route_to_workflow(
    state: State,
) -> Literal[
    "primary_assistant",
    "retrieve_metadata",
    "retrieve_semantics",
    "retrieve_docs",
    "retrieve_packages",
    "interact_admin_api",
]:
    """If we are in a delegated state, route directly to the appropriate assistant."""
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "primary_assistant"

    return dialog_state[-1]


def account_info(state: State):
    if state["account_info"] is None or state["account_info"] == "":
        list_accounts_tool = [
            tool for tool in dbt_tools.admin_api_tools if tool.name == "list_accounts"
        ][0]
        data = list_accounts_tool.invoke({})
        try:
            account = data[0]
        except IndexError:
            return {}

        if not account:
            return {}

        account_info = {
            "account_id": account["id"],
            "account_name": account["name"],
            "account_plan": account["plan"],
        }

        return {"account_info": account_info}

    return state


builder = StateGraph(State)


# Starting Point - Fetching Account Info for User
builder.add_node("fetch_account_info", account_info)
builder.add_edge(START, "fetch_account_info")

# Discovery API Assistant


def route_discovery_api(
    state: State,
) -> Literal["retrieve_metadata_tools", "leave_skill", "__end__"]:
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"

    return "retrieve_metadata_tools"


builder.add_node(
    "enter_discovery_api",
    create_entry_node("Discovery API Assistant", "retrieve_metadata"),
)
builder.add_node(
    "retrieve_metadata", DbtAssistant(dbt_runnables.discovery_api_runnable)
)
builder.add_edge("enter_discovery_api", "retrieve_metadata")
builder.add_node(
    "retrieve_metadata_tools",
    create_tool_node_with_fallback(dbt_tools.discovery_api_tools),
)
builder.add_edge("retrieve_metadata_tools", "retrieve_metadata")
builder.add_conditional_edges("retrieve_metadata", route_discovery_api)

# Semantic Layer Assistant


def route_semantic_layer(
    state: State,
) -> Literal["retrieve_semantic_tools", "leave_skill", "__end__"]:
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"

    return "retrieve_semantic_tools"


builder.add_node(
    "enter_semantic_layer",
    create_entry_node("Semantic Layer Assistant", "retrieve_semantics"),
)
builder.add_node(
    "retrieve_semantics", DbtAssistant(dbt_runnables.semantic_layer_runnable)
)
builder.add_edge("enter_semantic_layer", "retrieve_semantics")
builder.add_node(
    "retrieve_semantic_tools",
    create_tool_node_with_fallback(dbt_tools.semantic_layer_tools),
)
builder.add_edge("retrieve_semantic_tools", "retrieve_semantics")
builder.add_conditional_edges("retrieve_semantics", route_semantic_layer)

# Docs Assistant


def route_docs(
    state: State,
) -> Literal["retrieve_docs_tools", "leave_skill", "__end__"]:
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"

    return "retrieve_docs_tools"


builder.add_node("enter_docs", create_entry_node("Docs Assistant", "retrieve_docs"))
builder.add_node("retrieve_docs", DbtAssistant(dbt_runnables.docs_runnable))
builder.add_edge("enter_docs", "retrieve_docs")
builder.add_node(
    "retrieve_docs_tools", create_tool_node_with_fallback([dbt_tools.docs_tool])
)
builder.add_edge("retrieve_docs_tools", "retrieve_docs")
builder.add_conditional_edges("retrieve_docs", route_docs)

# Hub Assistant


def route_hub(
    state: State,
) -> Literal["retrieve_packages_tools", "leave_skill", "__end__"]:
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"

    return "retrieve_packages_tools"


builder.add_node("enter_hub", create_entry_node("Hub Assistant", "retrieve_packages"))
builder.add_node("retrieve_packages", DbtAssistant(dbt_runnables.hub_runnable))
builder.add_edge("enter_hub", "retrieve_packages")
builder.add_node(
    "retrieve_packages_tools",
    create_tool_node_with_fallback([dbt_tools.dbt_hub_retriever_tool]),
)
builder.add_edge("retrieve_packages_tools", "retrieve_packages")
builder.add_conditional_edges("retrieve_packages", route_hub)


# Hub Assistant


def route_admin_api(
    state: State,
) -> Literal["admin_api_tools", "leave_skill", "__end__"]:
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"

    return "admin_api_tools"


builder.add_node(
    "enter_admin_api", create_entry_node("Admin API Assistant", "interact_admin_api")
)
builder.add_node("interact_admin_api", DbtAssistant(dbt_runnables.admin_api_runnable))
builder.add_edge("enter_admin_api", "interact_admin_api")
builder.add_node(
    "admin_api_tools",
    create_tool_node_with_fallback(dbt_tools.admin_api_tools),
)
builder.add_edge("admin_api_tools", "interact_admin_api")
builder.add_conditional_edges("interact_admin_api", route_admin_api)

# Primary Assistant


def route_primary_assistant(
    state: State,
) -> Literal[
    "primary_assistant_tools",
    "enter_hub",
    "enter_docs",
    "enter_semantic_layer",
    "enter_discovery_api",
    "enter_admin_api",
    "__end__",
]:
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToDbtHubAssistant.__name__:
            return "enter_hub"

        if tool_calls[0]["name"] == ToDocsAssistant.__name__:
            return "enter_docs"

        if tool_calls[0]["name"] == ToSemanticLayerAssistant.__name__:
            return "enter_semantic_layer"

        if tool_calls[0]["name"] == ToDiscoveryApiAssistant.__name__:
            return "enter_discovery_api"

        if tool_calls[0]["name"] == ToAdminApiAssistant.__name__:
            return "enter_admin_api"

        return "primary_assistant_tools"

    raise ValueError("Invalid route.")


builder.add_node(
    "primary_assistant", DbtAssistant(dbt_runnables.primary_assistant_runnable)
)
builder.add_node(
    "primary_assistant_tools",
    create_tool_node_with_fallback(dbt_tools.primary_assistant_tools),
)
builder.add_conditional_edges(
    "primary_assistant",
    route_primary_assistant,
    {
        "enter_admin_api": "enter_admin_api",
        "enter_hub": "enter_hub",
        "enter_docs": "enter_docs",
        "enter_semantic_layer": "enter_semantic_layer",
        "enter_discovery_api": "enter_discovery_api",
        "primary_assistant_tools": "primary_assistant_tools",
        END: END,
    },
)
builder.add_edge("primary_assistant_tools", "primary_assistant")

# Reroute to current state
# TODO: This doesn't really work as expected.  It will just use the latest state
# and always reroute to that state, regardless of the intent of the user's next message.
# builder.add_conditional_edges("fetch_account_info", route_to_workflow)
builder.add_edge("fetch_account_info", "primary_assistant")

# Node shared for exiting all specialized assistants

builder.add_node("leave_skill", pop_dialog_state)
builder.add_edge("leave_skill", "primary_assistant")

memory = SqliteSaver.from_conn_string(":memory:")
graph = builder.compile(checkpointer=memory)
