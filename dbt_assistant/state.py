# stdlib
from typing import Annotated, Literal, Optional, Union

# third party
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


def update_dialog_stack(
    left: list[str], right: Optional[Union[str, list[str]]]
) -> list[str]:
    """Push or pop the state."""
    if right is None:
        return left

    if right == "pop":
        return left[:-1]

    if isinstance(right, list):
        return left + right

    return left + [right]


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    account_info: str
    dialog_state: Annotated[
        list[
            Literal[
                "primary_assistant",
                "retrieve_docs",
                "retrieve_semantics",
                "retrieve_metadata",
                "retrieve_packages",
                "interact_admin_api",
            ]
        ],
        update_dialog_stack,
    ]
