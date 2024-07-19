# stdlib
import os
import uuid

# third party=
from langchain_core.messages import HumanMessage

# first party
from dbt_assistant.graph import graph


def _print_event(event: dict, _printed: set, max_length=3000):
    current_state = next(iter(event))
    if current_state:
        print("Currently in: ", current_state)
    message = event[current_state].get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)


if __name__ == "__main__":
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    _printed = set()
    history = []
    print(f"Service token: {os.environ['DBT_CLOUD_SERVICE_TOKEN']}")
    while True:
        user = input("User (q/Q to quit): ")
        if user in {"q", "Q"}:
            print("AI: Byebye")
            break
        history.append(HumanMessage(content=user))
        for event in graph.stream({"messages": history}, config):
            _print_event(event, _printed)
