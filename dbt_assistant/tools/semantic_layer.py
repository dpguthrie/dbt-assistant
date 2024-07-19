# first party
from typing import Any, Union

# third party
from langchain_core.tools import tool

# first party
from dbt_assistant.tools.base_dbt_client import get_client


@tool
def get_dimensions_for_metrics(metrics: list[str]) -> Union[list[dict], str]:
    """Get a list of all dimensions for a given list of metrics in a user's dbt project.

    Args:
        metrics (list[str]): Names of metrics to get dimensions for.
    """
    client = get_client()
    response = client.sl.list_dimensions(metrics)
    try:
        dimensions = response.get("data", {}).get("dimensions", [])
    except (KeyError, AttributeError):
        return "No dimensions found in the response."

    if not dimensions:
        return "No dimensions found in the response."

    return dimensions


@tool
def get_dimension_values(dimension: str) -> Union[list[Any], str]:
    """Get a list of all values for a given dimension in a user's dbt project.

    Args:
        dimension (str): Name of the dimension to get values for.
    """
    client = get_client()
    qr = client.sl.list_dimension_values(group_by=[dimension], output_format="list")
    if qr.result:
        return [list(d.values())[0] for d in qr.result]

    return "No values found for the dimension."


@tool
def get_metrics() -> Union[list[dict], str]:
    """Get a list of all metrics in a user's dbt project."""
    client = get_client()
    response = client.sl.list_metrics()
    try:
        metrics = response.get("data", {}).get("metrics", [])
    except (KeyError, AttributeError):
        return "No metrics found in the response."

    if not metrics:
        return "No metrics found in the response."

    return metrics


semantic_layer_tools = [
    # get_metrics,
    # get_dimensions_for_metrics,
    get_dimension_values,
]
