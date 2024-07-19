# stdlib
from enum import Enum
from typing import Optional

# third party
from langchain_core.pydantic_v1 import BaseModel, Field


class CompleteOrEscalate(BaseModel):
    """
    A tool to mark the current task as completed and/or to escalate control of the
    dialog to the main assistant, who can re-route the dialog based on the user's needs.
    """

    cancel: bool = True
    reason: str

    class Config:
        schema_extra = {
            "example": {
                "cancel": True,
                "reason": "The user has requested to cancel the current task.",
            },
            "example_2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example_3": {
                "cancel": False,
                "reason": "I need to search through the docs for more information.",
            },
        }


class TimeGranularity(str, Enum):
    day = "DAY"
    week = "WEEK"
    month = "MONTH"
    quarter = "QUARTER"
    year = "YEAR"


class MetricInput(BaseModel):
    name: str = Field(description="The metric name as defined in the semantic layer.")


class GroupByInput(BaseModel):
    name: str = Field(
        description=(
            "The dimension name as defined in the semantic layer. "
            "A common dimension used here will be metric_time.  This will ALWAYS have "
            "an associated grain."
        )
    )
    grain: Optional[TimeGranularity] = Field(
        default=None,
        description=(
            "Grain should only be used for date/time fields, including metric_time."
        ),
    )

    class Config:
        use_enum_values = True


class MetricOrderByInput(BaseModel):
    metric: MetricInput
    descending: Optional[bool] = None


class GroupByOrderByInput(BaseModel):
    groupBy: GroupByInput
    descending: Optional[bool] = None


class WhereInput(BaseModel):
    sql: str


class Query(BaseModel):
    metrics: list[MetricInput]
    groupBy: Optional[list[GroupByInput]] = None
    where: Optional[list[WhereInput]] = None
    metricOrderBy: Optional[list[MetricOrderByInput]] = None
    groupByOrderBy: Optional[list[GroupByOrderByInput]] = None
    limit: Optional[int] = None


class ToDiscoveryApiAssistant(BaseModel):
    """
    Transfers work to a specialized assistant to handle requests to the Discovery API.
    """

    request: str = Field(
        description=(
            "Any additional information or requests from the user regarding "
            "the metadata around their dbt project."
        )
    )

    class Config:
        schema_extra = {
            "example": {
                "request": "What are the downstream models from my total revenue model?"
            },
            "example_2": {
                "request": (
                    "How has performance of my fact orders model changed since its "
                    "last update?"
                ),
            },
        }


class ToSemanticLayerAssistant(BaseModel):
    """
    Transfers work to a specialized assistant to handle requests to the Semantic Layer.
    """

    request: str = Field(
        description=(
            "Any additional information or requests from the user regarding "
            "the semantics (semantic models, dimensions, metrics, entities) of their "
            "dbt project."
        )
    )

    class Config:
        schema_extra = {
            "example": {
                "request": "Who is the highest performing sales clerk by profit in 2023?"
            },
            "example_2": {
                "request": ("What entities are defined in my total revenue metric?"),
            },
        }


class ToDocsAssistant(BaseModel):
    """
    Transfers work to a specialized assistant to handle requests to the dbt
    documentation.
    """

    request: str = Field(
        description=(
            "Any additional information or requests from the user regarding "
            "information related to dbt's documentation."
        )
    )

    class Config:
        schema_extra = {
            "example": {"request": "What is a semantic model?"},
            "example_2": {
                "request": ("How can I define an incremental model?"),
            },
            "example_3": {
                "request": ("How should I structure my staging layer?"),
            },
        }


class ToDbtHubAssistant(BaseModel):
    """
    Transfers work to a specialized assistant to handle requests to dbt's hub (a
    place where users can download packages containing macros, tests, and models).
    """

    request: str = Field(
        description=(
            "Any additional information or requests from the user regarding "
            "information related to dbt Hub."
        )
    )

    class Config:
        schema_extra = {
            "example": {"request": "What packages offer tests for schema changes"},
            "example_2": {
                "request": ("What packages are available for anomaly detection?"),
            },
        }


class ToAdminApiAssistant(BaseModel):
    """
    Transfers work to a specialized assistant to handle requests to dbt Cloud's
    Administrative API.
    """

    request: str = Field(
        description=(
            "Any additional information or requests from the user regarding "
            "information related to dbt Cloud's Administrative API."
        )
    )

    class Config:
        schema_extra = {
            "example": {"request": "When was the last time I had a run that errored?"},
            "example_2": {
                "request": ("Can you create a job for me that runs every hour?"),
            },
        }


primary_assistant_tools = [
    ToAdminApiAssistant,
    ToDbtHubAssistant,
    ToDiscoveryApiAssistant,
    ToDocsAssistant,
    ToSemanticLayerAssistant,
]
