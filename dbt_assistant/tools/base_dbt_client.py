# stdlib
import os
from typing import Optional, Type

# third party
from dbtc import dbtCloudClient
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

# first party
from dbt_assistant.utils.dbt_cloud import DbtCloudApiWrapper


def get_client():
    try:
        token = os.environ["DBT_CLOUD_SERVICE_TOKEN"]
    except KeyError:
        raise Exception(
            "Both DBT_CLOUD_ENVIRONMENT_ID and DBT_CLOUD_SERVICE_TOKEN environment "
            "variables must be set."
        )
    environment_id = os.getenv("DBT_CLOUD_ENVIRONMENT_ID", None)
    host = os.getenv("DBT_CLOUD_HOST", "cloud.getdbt.com")
    return dbtCloudClient(service_token=token, environment_id=environment_id, host=host)


class DbtCloudAction(BaseTool):
    """Tool for interacting with the dbt Cloud APIs."""

    api_wrapper: DbtCloudApiWrapper = Field(default_factory=DbtCloudApiWrapper)  # type: ignore[arg-type]
    mode: str
    name: str = ""
    description: str = ""
    args_schema: Optional[Type[BaseModel]] = None

    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs):
        """Use the dbt Cloud API to run an operation."""
        return self.api_wrapper.run(self.mode, **kwargs)
