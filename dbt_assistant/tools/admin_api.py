# first party
from typing import List, Literal, Optional, Union

# third party
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool

# first party
from dbt_assistant.tools.base_dbt_client import get_client


class Webhook(BaseModel):
    active: bool = Field(
        ..., description="Whether or not this Webhooks is currently active."
    )
    client_url: str = Field(..., description="Endpoint where events are sent.")
    event_types: List[
        Literal["job.run.started", "job.run.completed", "job.run.errored"]
    ] = Field(
        ...,
        description="Event types that triger this webhook.  Must not be empty.",
    )
    name: str = Field(..., description="Webhook name")

    deactivate_reason: Optional[str] = Field(
        default=None,
        description="Reason for deactivation",
    )
    description: Optional[str] = Field(default=None, description="Webhook description")
    id: Optional[str] = None
    job_ids: Optional[int] = Field(
        default=None,
        description="Job IDs that trigger this webhook.  Leave empty to trigger for all jobs.",
    )


class Environment(BaseModel):
    id: Optional[int] = None
    account_id: int = Field(..., description="Id of the account")
    project_id: int = Field(..., description="Id of the project")
    credentials_id: int = Field(None, description="Id of the credentials")
    extended_attributes_id: int = Field(
        None, description="Id of the extended attributes"
    )
    name: str = Field(..., description="Name of the environment")
    dbt_version: str = Field(..., description="Version of dbt")
    type: Literal["deployment", "development"] = Field(
        ..., description="Type of environment"
    )
    use_custom_branch: bool = Field(
        ..., description="Whether or not to use a custom branch"
    )
    custom_branch: str = Field(None, description="Custom branch to use")
    supports_docs: bool = Field(
        ..., description="Whether or not the environment supports docs"
    )
    state: Literal[1, 2] = Field(1, description="1 = active, 2 = deleted")
    deployment_type: Literal["production", "staging"] = Field(
        None, description="Type of deployment"
    )


class EnvironmentVariable(BaseModel):
    account_id: int = Field(..., description="Id of the account")
    project_id: int = Field(..., description="Id of the project")
    name: str = Field(..., description="Name of the environment variable")
    type: List[Literal["project", "environment", "job", "user"]] = Field(
        ..., description="Type of the environment variable"
    )
    state: int = Field(1, description="1 = active, 2 = deleted")
    user_id: int = Field(None, description="Id of the user")
    environment_id: int = Field(None, description="Id of the environment")
    job_definition_id: int = Field(None, description="Id of the Job")
    raw_value: str = Field(None, description="Raw value of the environment variable")
    display_value: str = Field(
        None, description="Display value of the environment variable"
    )


class ExtendedAttribute(BaseModel):
    account_id: int = Field(..., description="Id of the account")
    project_id: int = Field(..., description="Id of the project")
    id: Optional[int] = Field(None, description="Id of the extended attribute")
    extended_attributes: str = Field(..., description="Extended attributes")
    state: Literal[1, 2] = Field(1, description="1 = active, 2 = deleted")


class Group(BaseModel):
    account_id: int = Field(..., description="Id of the account")
    name: str = Field(..., description="Name of the group")
    assign_by_default: bool = Field(
        ..., description="Whether or not users should be assigned by default"
    )
    id: Optional[int] = Field(None, description="Id of the group")
    state: Optional[int] = Field(1, description="1 = active, 2 = deleted")
    sso_mapping_groups: Optional[list[str]] = Field(
        None, description="List of SSO mapping groups"
    )


class TriggerJob(BaseModel):
    cause: str = Field(..., description="The cause of the job trigger")
    git_sha: str = Field(None, description="The git SHA to be used for the job trigger")
    git_branch: str = Field(
        None, description="The git branch to be used for the job trigger"
    )
    azure_pull_request_id: int = Field(
        None, description="The Azure pull request ID to be used for the job trigger"
    )
    github_pull_request_id: int = Field(
        None, description="The GitHub pull request ID to be used for the job trigger"
    )
    gitlab_merge_request_id: int = Field(
        None, description="The GitLab merge request ID to be used for the job trigger"
    )
    schema_override: str = Field(
        None, description="The schema override to be used for the job trigger"
    )
    dbt_version_override: str = Field(
        None, description="The dbt version override to be used for the job trigger"
    )
    threads_override: str = Field(
        None, description="The threads override to be used for the job trigger"
    )
    target_name_override: str = Field(
        None, description="The target name override to be used for the job trigger"
    )
    generate_docs_override: bool = Field(
        None, description="Whether to generate docs for the job trigger"
    )
    timeout_seconds_override: int = Field(
        None, description="The timeout seconds override to be used for the job trigger"
    )
    steps_override: list[str] = Field(
        None,
        description="The dbt commands to be used for the job trigger (overriding what job has defined.)",
    )


def _is_success(response: dict) -> bool:
    """Check if a response from the dbt Cloud API is successful.

    Args:
        response (dict): Response from the dbt Cloud API.

    Returns:
        bool: True if the response is successful, False otherwise.
    """
    return response["status"]["is_success"]


def _simple_return(response: dict) -> list[dict]:
    if _is_success(response):
        return response["data"]

    try:
        return [{"error": response["status"]["user_message"]}]
    except KeyError:
        return [{"error": "An unknown error occurred."}]


# Cancel Tools


@tool
def cancel_run(account_id: int, run_id: int) -> dict:
    """Cancel a run."""
    client = get_client()
    response = client.cloud.cancel_run(account_id=account_id, run_id=run_id)
    return response


# Create Tools


@tool
def create_environment_variables(
    account_id: int, project_id: int, payload: EnvironmentVariable
):
    """Create environment variables for a specified project.

    Args:
        account_id (int): Numeric ID of the account to retrieve
        project_id (int): Numeric ID of the project to retrieve
        payload (dict): The environment variable to create
    """
    client = get_client()
    return client.cloud.create_env_vars(
        account_id=account_id, project_id=project_id, payload=payload
    )


@tool
def create_environment(account_id: int, project_id: int, payload: Environment):
    """Create an environment for a specified project.

    Args:
        account_id (int): Numeric ID of the account to retrieve
        project_id (int): Numeric ID of the project to retrieve
        payload (Environment): The environment to create
    """
    client = get_client()
    return client.cloud.create_environment(
        account_id=account_id, project_id=project_id, payload=payload.dict()
    )


@tool
def create_extended_attributes(
    account_id: int, project_id: int, payload: ExtendedAttribute
):
    """Create extended attributes for a specified project.

    Args:
        account_id (int): Numeric ID of the account to retrieve
        project_id (int): Numeric ID of the project to retrieve
        payload (ExtendedAttribute): The extended attributes to create
    """
    client = get_client()
    return client.cloud._simple_request(
        path=f"accounts/{account_id}/projects/{project_id}/extended-attributes/",
        method="post",
        json=payload.dict(),
    )


@tool
def create_webhook(account_id: int, payload: Webhook):
    """Create a webhook for a specified account.

    Args:
        account_id (int): Numeric ID of the account to retrieve
        payload (Webhook): The webhook to create
    """
    client = get_client()
    response = client.cloud.create_webhook(
        account_id=account_id, payload=payload.dict()
    )
    return response


# Get Tools


@tool
def get_account_licenses(account_id: int) -> dict:
    """List account licenses for a specified account."""
    client = get_client()
    response = client.cloud.get_account_licenses(account_id=account_id)
    return _simple_return(response)


@tool
def get_job(account_id: int, job_id: int) -> dict:
    """Get a job by its ID."""
    client = get_client()
    response = client.cloud.get_job(account_id=account_id, job_id=job_id)
    return response


@tool
def get_run(account_id: int, run_id: int) -> dict:
    """Get a run by its ID."""
    client = get_client()
    response = client.cloud.get_run(account_id=account_id, run_id=run_id)
    return response


@tool
def get_run_artifact(
    account_id: int,
    run_id: int,
    path: str,
    *,
    step: int = None,
) -> Union[str, dict]:
    """Fetch artifacts from a completed run.

    Once a run has completed, you can use this endpoint to download the
    `manifest.json`, `run_results.json` or `catalog.json` files from dbt Cloud.

    !!! note
        By default, this endpoint returns artifacts from the last step in the
        run. To list artifacts from other steps in the run, use the step query
        parameter described below.


    Args:
        account_id (int): Numeric ID of the account to retrieve
        run_id (int): Numeric ID of the run to retrieve
        path (str): Paths are rooted at the target/ directory. Use manifest.json,
            catalog.json, or run_results.json to download dbt-generated artifacts
            for the run.
        step (str, optional): The index of the Step in the Run to query for
            artifacts. The first step in the run has the index 1. If the step
            parameter is omitted, then this endpoint will return the artifacts
            compiled for the last step in the run.
    """
    client = get_client()
    response = client.cloud.get_run_artifact(
        account_id=account_id,
        run_id=run_id,
        path=path,
        step=step,
    )
    return response


# List Tools


@tool
def list_accounts() -> list[dict]:
    """List all accounts a user is associated with."""
    client = get_client()
    response = client.cloud.list_accounts()
    return _simple_return(response)


@tool
def list_audit_logs(
    account_id: int,
    *,
    logged_at_start: str = None,
    logged_at_end: str = None,
    offset: int = None,
    limit: int = None,
):
    """List audit logs for a specific account

    !!! note
        This API is only available to enterprise customers.

    Args:
        account_id (int): Numeric ID of the account to retrieve
        logged_at_start (str, optional):  Date to begin retrieving audit
            logs.  Format is yyyy-mm-dd
        logged_at_end (str, optional): Date to stop retrieving audit logs.
            Format is yyyy-mm-dd
        offset (int, optional): The offset to apply when listing runs.
            Use with limit to paginate results.
        limit (int, optional): The limit to apply when listing runs.
            Use with offset to paginate results.
    """
    client = get_client()
    response = client.cloud.list_audit_logs(
        account_id=account_id,
        logged_at_start=logged_at_start,
        logged_at_end=logged_at_end,
        offset=offset,
        limit=limit,
    )
    return _simple_return(response)


@tool
def list_connections(
    account_id: int,
    project_id: int,
    *,
    state: int = None,
    offset: int = None,
    limit: int = None,
) -> dict:
    """List connections for a specific account and project"""
    client = get_client()
    response = client.cloud.list_connections(
        account_id=account_id,
        project_id=project_id,
        state=state,
        offset=offset,
        limit=limit,
    )
    return _simple_return(response)


@tool
def list_credentials(account_id: int, project_id: int) -> dict:
    """List credentials for a specific account and project."""
    client = get_client()
    response = client.cloud.list_credentials(
        account_id=account_id, project_id=project_id
    )
    return _simple_return(response)


@tool
def list_environment_variables(
    account_id: int,
    project_id: int,
    *,
    resource_type: Optional[Literal["environment", "job", "user"]] = "environment",
    environment_id: int = None,
    job_id: int = None,
    limit: int = 100,
    offset: int = None,
    name: str = None,
    state: int = None,
    user_id: int = None,
) -> list[dict]:
    """List environment variables for a specific account and project"""
    client = get_client()
    response = client.cloud.list_environment_variables(
        account_id=account_id,
        project_id=project_id,
        resource_type=resource_type,
        environment_id=environment_id,
        job_id=job_id,
        limit=limit,
        offset=offset,
        name=name,
        state=state,
        user_id=user_id,
    )
    return _simple_return(response)


@tool
def list_environments(
    account_id: int,
    project_id: int,
    *,
    dbt_version: str = None,
    deployment_type: Literal["production", "staging"] = None,
    credentials_id: int = None,
    name: str = None,
    type: Literal["deployment", "development"] = None,
    state: Literal[1, 2] = None,
    offset: int = None,
    limit: int = None,
    order_by: str = None,
) -> dict:
    """List environments for a specific account and project"""
    client = get_client()
    response = client.cloud.list_environments(
        account_id=account_id,
        project_id=project_id,
        dbt_version=dbt_version,
        deployment_type=deployment_type,
        credentials_id=credentials_id,
        name=name,
        type=type,
        state=state,
        offset=offset,
        limit=limit,
        order_by=order_by,
    )
    return _simple_return(response)


@tool
def list_groups(account_id: int) -> dict:
    """List groups for a specific account and project"""
    client = get_client()
    response = client.cloud.list_groups(account_id=account_id)
    return _simple_return(response)


@tool
def list_invited_users(account_id: int) -> dict:
    """List invited users in an account."""
    client = get_client()
    response = client.cloud.list_invited_users(account_id=account_id)
    return _simple_return(response)


@tool
def list_jobs(
    account_id: int,
    *,
    environment_id: int = None,
    project_id: int = None,
    state: Literal[1, 2] = None,
    offset: int = None,
    limit: int = None,
    order_by: str = None,
) -> dict:
    """List jobs in an account, specific project, or environment."""
    client = get_client()
    response = client.cloud.list_jobs(
        account_id=account_id,
        environment_id=environment_id,
        project_id=project_id,
        state=state,
        offset=offset,
        limit=limit,
        order_by=order_by,
    )
    return _simple_return(response)


@tool
def list_projects(
    account_id: int,
    *,
    project_id: int = None,
    state: int = None,
    offset: int = None,
    limit: int = None,
) -> list[dict]:
    """List projects for a specified account.

    Args:
        account_id (int): Numeric ID of the account to retrieve
        project_id (int, optional): The project ID to retrieve
        state (int, optional): 1 = active, 2 = deleted
        offset (int, optional): The offset to apply when listing projects.
            Use with limit to paginate results.
        limit (int, optional): The limit to apply when listing projects.
            Use with offset to paginate results.
    """
    client = get_client()
    response = client.cloud.list_projects(
        account_id=account_id,
        project_id=project_id,
        state=state,
        offset=offset,
        limit=limit,
    )
    return _simple_return(response)


@tool
def list_run_artifacts(
    account_id: int,
    run_id: int,
    *,
    step: int = None,
) -> dict:
    """Fetch a list of artifact files generated for a completed run.

    Args:
        account_id (int): Numeric ID of the account to retrieve
        run_id (int): Numeric ID of the run to retrieve
        step (str, optional): The index of the Step in the Run to query for
            artifacts. The first step in the run has the index 1. If the step
            parameter is omitted, then this endpoint will return the artifacts
            compiled for the last step in the run.
    """
    client = get_client()
    response = client.cloud.list_run_artifacts(
        account_id=account_id,
        run_id=run_id,
        step=step,
    )
    return _simple_return(response)


@tool
def list_runs(
    account_id: int,
    *,
    include_related: List[str] = None,
    job_definition_id: int = None,
    environment_id: int = None,
    project_id: int = None,
    deferring_run_id: int = None,
    status: Literal[
        "queued", "starting", "running", "success", "error", "cancelled"
    ] = None,
    order_by: str = None,
    offset: int = None,
    limit: int = None,
) -> dict:
    """List runs in an account.

    Args:
        include_related (list): List of related
            fields to pull with the run. Valid values are `trigger`, `job`,
            `repository`, `debug_logs`, `run_steps`, and `environment`.
        job_definition_id (int, optional): Applies a filter to only return
            runs from the specified Job.
        deferring_run_id (int, optional): Numeric ID of a deferred run
        status (str or list, optional): The status to apply when listing runs.
            Options include queued, starting, running, success, error, and
            cancelled
        order_by (str, optional): Field to order the result by.
            Use - to indicate reverse order.
        offset (int, optional): The offset to apply when listing runs.
            Use with limit to paginate results.
        limit (int, optional): The limit to apply when listing runs.
            Use with offset to paginate results.
    """
    client = get_client()
    response = client.cloud.list_runs(
        account_id=account_id,
        include_related=include_related,
        job_definition_id=job_definition_id,
        environment_id=environment_id,
        project_id=project_id,
        deferring_run_id=deferring_run_id,
        status=status,
        order_by=order_by,
        offset=offset,
        limit=limit,
    )
    return _simple_return(response)


@tool
def list_service_token_permissions(account_id: int, service_token_id: int) -> dict:
    """List service token permissions for a specific account."""
    client = get_client()
    response = client.cloud.list_service_token_permissions(
        account_id=account_id, service_token_id=service_token_id
    )
    return _simple_return(response)


@tool
def list_service_tokens(account_id: int) -> dict:
    """List service tokens for a specific account."""
    client = get_client()
    response = client.cloud.list_service_tokens(account_id=account_id)
    return _simple_return(response)


@tool
def list_users(
    account_id: int,
    *,
    state: Literal[1, 2] = None,
    limit: int = None,
    offset: int = None,
    order_by: str = "email",
) -> dict:
    """List users in an account.

    Args:
        account_id (int): Numeric ID of the account to retrieve
        state (int, optional): 1 = active, 2 = deleted
        limit (int, optional): The limit to apply when listing runs.
            Use with offset to paginate results.
        offset (int, optional): The offset to apply when listing runs.
            Use with limit to paginate results.
        order_by (str, optional): Field to order the result by.
            Use - to indicate reverse order.
    """
    client = get_client()
    response = client.cloud.list_users(
        account_id=account_id,
        state=state,
        limit=limit,
        offset=offset,
        order_by=order_by,
    )
    return _simple_return(response)


@tool
def list_webhooks(account_id: int, *, limit: int = None, offset: int = None) -> dict:
    """List of webhooks in account."""
    client = get_client()
    response = client.cloud.list_webhooks(
        account_id=account_id,
        limit=limit,
        offset=offset,
    )
    return _simple_return(response)


# Trigger Tools


@tool
def trigger_job(
    account_id: int,
    job_id: int,
    payload: TriggerJob,
) -> dict:
    """Trigger a job by its ID."""
    client = get_client()
    response = client.cloud.trigger_job(
        account_id=account_id, job_id=job_id, payload=payload.dict(), should_poll=False
    )
    return response


admin_api_safe_tools = [
    get_account_licenses,
    get_job,
    get_run,
    get_run_artifact,
    list_accounts,
    list_audit_logs,
    list_connections,
    list_credentials,
    list_environment_variables,
    list_environments,
    list_groups,
    list_invited_users,
    list_jobs,
    list_projects,
    list_run_artifacts,
    list_runs,
    list_service_token_permissions,
    list_service_tokens,
    list_users,
    list_webhooks,
]

admin_api_unsafe_tools = [
    cancel_run,
    create_environment_variables,
    create_environment,
    create_extended_attributes,
    create_webhook,
    trigger_job,
]

admin_api_tools = admin_api_safe_tools + admin_api_unsafe_tools
