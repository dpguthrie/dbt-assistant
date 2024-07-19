# first party
import os
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Tuple, Union

# third party
from langchain_core.tools import tool

# first party
from dbt_assistant.tools.base_dbt_client import get_client

FIRST_N_RESULTS = 500
DEFAULT_DAYS_AGO = 14
MAXIMUM_DAYS_AGO = 90


def _create_date_range(start_date: str = None, end_date: str = None) -> Tuple[str, str]:
    today = datetime.now().date()
    default_start_date = today - timedelta(days=DEFAULT_DAYS_AGO)
    minimum_start_date = today - timedelta(days=MAXIMUM_DAYS_AGO)

    # Process start_date
    if start_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            start_date = max(start_date, minimum_start_date)
        except ValueError:
            # If there's an error parsing the date, default to two weeks ago
            start_date = default_start_date
    else:
        start_date = default_start_date

    # Process end_date
    if end_date:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            end_date = min(end_date, today)
        except ValueError:
            # If there's an error parsing the date, default to today
            end_date = today
    else:
        end_date = today

    # Ensure end_date is not before start_date
    if end_date < start_date:
        end_date = start_date

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def _extract_nested_edges(
    response: Union[List[Dict], Dict],
    keys: List[str],
    *,
    error_message: str = "Nothing found.",
):
    # If response is a dictionary, wrap it in a list
    if isinstance(response, dict):
        response = [response]

    all_edges = []

    for item in response:
        # Navigate through the nested structure
        current = item
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                # If we can't find the complete path, return the error message
                print(f"An error seems to have occurred.  See response:\n{response}")
                return error_message

        # If we've successfully navigated to 'edges' extend our list
        if isinstance(current, list):
            all_edges.extend(current)

    return all_edges


@tool
def get_longest_executed_models(
    environment_id: int = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 5,
    job_limit: int = 5,
    job_id: int = None,
    order_by: Literal["AVG", "MAX"] = "MAX",
) -> Union[List[Dict], str]:
    """Get a list of the longest executed models for a given timeframe (defaults to the
    last 2 weeks) in a user's dbt Cloud project.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
        start_date (str, optional): Start date in the format YYYY-MM-DD.
            Defaults to None.
        end_date (str, optional): End date in the format YYYY-MM-DD.
            Defaults to None
        limit (int, optional): Number of models to return. Defaults to 5.
        job_limit (int, optional): Limit the number of jobs to return for each model.
            Defaults to 5.
        job_id (int, optional): Filter by a specific job ID. Defaults to None.
        order_by ("MAX", "AVG", optional): How to order results. Defaults to "MAX".
    """
    client = get_client()
    start_date, end_date = _create_date_range(start_date, end_date)
    response = client.metadata.longest_executed_models(
        environment_id=int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        job_limit=job_limit,
        job_id=job_id,
        order_by=order_by,
    )
    return _extract_nested_edges(
        response, ["data", "performance", "longestExecutedModels"]
    )


@tool
def get_model_performance_history(
    unique_id: str,
    *,
    start_date: str = None,
    end_date: str = None,
    environment_id: int = None,
) -> Union[List[Dict], str]:
    """Get the model performance (or execution history) for a given model in a user's
    dbt project.

    Args:
        unique_id (str): Unique ID of the model.
        start_date (str, optional): Start date in the format YYYY-MM-DD.
            Defaults to None.
        end_date (str, optional): End date in the format YYYY-MM-DD.
            Defaults to None.
        environment_id (int, optional): Environment ID. Defaults to None.
    """
    client = get_client()
    start_date, end_date = _create_date_range(start_date, end_date)
    response = client.metadata.model_execution_history(
        unique_id=unique_id,
        start_date=start_date,
        end_date=end_date,
        environment_id=int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
    )
    return _extract_nested_edges(
        response, ["data", "performance", "modelExecutionHistory"]
    )


@tool
def get_most_executed_models(
    environment_id: int = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 5,
    job_limit: int = 5,
) -> Union[List[Dict], str]:
    """Get a list of the most executed models for a given timeframe (defaults to the
    last 2 weeks) in a user's dbt Cloud project.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
        start_date (str, optional): Start date in the format YYYY-MM-DD.
            Defaults to None.
        end_date (str, optional): End date in the format YYYY-MM-DD.
            Defaults to None.
        limit (int, optional): Number of models to return. Defaults to 5.
        job_limit (int, optional): Limit the number of jobs to return for each model.
            Defaults to 5.
    """
    client = get_client()
    start_date, end_date = _create_date_range(start_date, end_date)
    response = client.metadata.most_executed_models(
        environment_id=int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        job_limit=job_limit,
    )
    return _extract_nested_edges(
        response, ["data", "performance", "mostExecutedModels"]
    )


@tool
def get_most_failed_models(
    environment_id: int = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 5,
) -> Union[List[Dict], str]:
    """Get a list of the most failed models for a given timeframe (defaults to the
    last 2 weeks) in a user's dbt Cloud project.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
        start_date (str, optional): Start date in the format YYYY-MM-DD.
            Defaults to None.
        end_date (str, optional): End date in the format YYYY-MM-DD.
            Defaults to None.
        limit (int, optional): Number of models to return. Defaults to 5.
    """
    client = get_client()
    start_date, end_date = _create_date_range(start_date, end_date)
    response = client.metadata.most_failed_models(
        environment_id=int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return _extract_nested_edges(response, ["data", "performance", "mostFailedModels"])


@tool
def get_consumer_projects(environment_id: int = None) -> Union[List[Dict], str]:
    """
    Get a list of consumer projects in a user's dbt Cloud account.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
    """
    client = get_client()
    query = """
    query Environment($environmentId: BigInt!) {
    environment(id: $environmentId) {
        consumerProjects {
        consumerCloudProject
        consumerCoreProject
        consumerEnvironmentId
        consumerProjectId
        producerPublicModels {
            numEdges
            uniqueId
        }
        }
    }
    }
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"])
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(response, ["data", "environment", "consumerProjects"])


@tool
def get_exposures(
    unique_ids: List[str],
    *,
    environment_id: int = None,
    exposure_type: str = None,
    tags: List[str] = None,
):
    """Get a list of exposures in a user's dbt Cloud account.

    Args:
        unique_ids (List[str], required): Filter by unique IDs.
        environment_id (int, optional): Environment ID. Defaults to None.
        exposure_type (str, optional): Filter by exposure type. Defaults to None.
        tags (List[str], optional): Filter by tags. Defaults to None.
    """
    client = get_client()
    query = """
    query Environment($environmentId: BigInt!, $after: String, $filter: ExposureFilter, $first: Int) {
    environment(id: $environmentId) {
        applied {
        exposures(after: $after, filter: $filter, first: $first) {
            pageInfo {
            endCursor
            hasNextPage
            hasPreviousPage
            startCursor
            }
            totalCount
            edges {
            cursor
            node {
                description
                exposureType
                label
                maturity
                meta
                name
                ownerEmail
                ownerName
                packageName
                resourceType
                tags
                uniqueId
                url
            }
            }
        }
        }
    }
    }
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "first": FIRST_N_RESULTS,
        "after": None,
        "filter": {
            "exposureType": exposure_type,
            "tags": tags,
            "uniqueIds": unique_ids,
        },
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "environment", "applied", "exposures", "edges"]
    )


@tool
def get_models(
    unique_ids: List[str],
    *,
    environment_id: int = None,
    access: str = None,
    database: str = None,
    group: str = None,
    identifier: str = None,
    last_run_status: Literal["error", "skipped", "success"] = None,
    modeling_layer: str = None,
    package_name: str = None,
    database_schema: str = None,
    tags: List[str] = None,
) -> List[Dict]:
    """Get a list of models by unique_id in a user's dbt Cloud project.

    Args:
        unique_ids (List[str], required): Filter by unique IDs.
        environment_id (int, optional): Environment ID. Defaults to None.
        access (str, optional): Filter by model access. Defaults to None.
        database (str, optional): Filter by database. Defaults to None.
        group (str, optional): Filter by group. Defaults to None.
        identifier (str, optional): Filter by identifier. Defaults to None.
        last_run_status (Literal["error", "skipped", "success"], optional): Filter by
            last run status. Defaults to None.
        database_schema (str, optional): Filter by schema. Defaults to None.
        tags (List[str], optional): Filter by tags. Defaults to None.
    """
    client = get_client()
    query = """
    query Environment($environmentId: BigInt!, $after: String, $filter: ModelAppliedFilter, $first: Int, $types: [AncestorNodeType!]!) {
    environment(id: $environmentId) {
        applied {
        models(after: $after, filter: $filter, first: $first) {
            pageInfo {
            endCursor
            hasNextPage
            hasPreviousPage
            startCursor
            }
            totalCount
            edges {
            cursor
            node {
                access
                alias
                ancestors(types: $types) {
                    description
                    name
                    resourceType
                    uniqueId
                }
                catalog {
                columns {
                    description
                    name
                    type
                }
                rowCountStat
                stats {
                    description
                    label
                    value
                }
                }
                children {
                    description
                    name
                    resourceType
                    uniqueId
                }
                database
                dbtVersion
                deprecationDate
                description
                executionInfo {
                    compileCompletedAt
                    compileStartedAt
                    executeCompletedAt
                    executeStartedAt
                    executionTime
                    lastJobDefinitionId
                    lastRunError
                    lastRunGeneratedAt
                    lastRunId
                    lastRunStatus
                    lastSuccessJobDefinitionId
                    lastSuccessRunId
                    runElapsedTime
                    runGeneratedAt
                }
                fqn
                group
                language
                materializedType
                meta
                modelingLayer
                name
                packageName
                resourceType
                schema
                tags
                uniqueId
                usageQueryCount
            }
            }
        }
        }
    }
    }
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "first": FIRST_N_RESULTS,
        "after": None,
        "types": ["Model", "Source", "Snapshot", "Seed"],
        "filter": {
            "access": access,
            "database": database,
            "group": group,
            "identifier": identifier,
            "lastRunStatus": last_run_status,
            "modelingLayer": modeling_layer,
            "packageName": package_name,
            "schema": database_schema,
            "tags": tags,
            "uniqueIds": unique_ids,
        },
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "environment", "applied", "models", "edges"]
    )


@tool
def get_recent_resource_changes(
    environment_id: int = None,
    number_of_days: int = 7,
) -> List[Dict]:
    """Get a list of recent resource changes in a user's dbt Cloud project.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
        number_of_days (int, optional): Number of days to look back. Defaults to 7.
    """
    client = get_client()
    query = """
    query Environment($environmentId: BigInt!, $after: String, $first: Int, $numDays: Int!) {
    environment(id: $environmentId) {
        applied {
        recentResourceChanges(after: $after, first: $first, numDays: $numDays) {
            totalCount
            pageInfo {
            endCursor
            hasNextPage
            hasPreviousPage
            startCursor
            }
            edges {
            cursor
            node {
                changes
                accountId
                environmentId
                gitSha
                jobDefinitionId
                mostRecentChangedAt
                projectId
                resource {
                ... on ExposureAppliedStateNestedNode {
                    name
                    resourceType
                    uniqueId
                }
                ... on ExternalModelNode {
                    name
                    resourceType
                    uniqueId
                }
                ... on MacroDefinitionNestedNode {
                    name
                    resourceType
                    uniqueId
                }
                ... on MetricDefinitionNestedNode {
                    name
                    resourceType
                    uniqueId
                }
                ... on ModelAppliedStateNestedNode {
                    name
                    resourceType
                    uniqueId
                }
                ... on SeedAppliedStateNestedNode {
                    name
                    resourceType
                    uniqueId
                }
                ... on SemanticModelDefinitionNestedNode {
                    name
                    resourceType
                    uniqueId
                }
                ... on SnapshotAppliedStateNestedNode {
                    name
                    resourceType
                    uniqueId
                }
                ... on SourceAppliedStateNestedNode {
                    name
                    resourceType
                    uniqueId
                }
                ... on TestAppliedStateNestedNode {
                    name
                    resourceType
                    uniqueId
                }
                }
                runId
                uniqueId
            }
            }
        }
        }
    }
    }
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "first": FIRST_N_RESULTS,
        "after": None,
        "numDays": number_of_days,
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "environment", "applied", "recentResourceChanges", "edges"]
    )


@tool
def get_resource_counts(environment_id: int = None) -> Dict:
    """Get a count of resources in a user's dbt Cloud project.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
    """
    client = get_client()
    query = """
    query Environment($environmentId: BigInt!) {
    environment(id: $environmentId) {
        applied {
        resourceCounts
        }
    }
    }
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"])
    }
    response = client.metadata.query(query, variables)
    return response["data"]["environment"]["applied"]["resourceCounts"]


@tool
def get_project_tags(environment_id: int = None) -> List[Dict]:
    """Get a list of project tags in a user's dbt Cloud project.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
    """
    client = get_client()
    query = """
    query Environment($environmentId: BigInt!) {
    environment(id: $environmentId) {
        applied {
        tags {
            name
        }
        }
    }
    }
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"])
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(response, ["data", "environment", "applied", "tags"])


@tool
def get_sources(
    unique_ids: List[str],
    *,
    environment_id: int = None,
    database: str = None,
    freshness_checked: bool = None,
    database_schema: str = None,
    source_names: List[str] = None,
    tags: List[str] = None,
) -> List[Dict]:
    """Get a list of sources in a user's dbt Cloud project.

    Args:
        unique_ids (List[str], required): Filter by unique IDs.
        environment_id (int, optional): Environment ID. Defaults to None.
        database (str, optional): Filter by database. Defaults to None.
        freshness_checked (bool, optional): Filter by freshness checked. Defaults to None.
        database_schema (str, optional): Filter by schema. Defaults to None.
        source_names (List[str], optional): Filter by source names. Defaults to None.
        tags (List[str], optional): Filter by tags. Defaults to None.
    """
    client = get_client()
    query = """
query Environment($environmentId: BigInt!, $after: String, $filter: SourceAppliedFilter, $first: Int) {
  environment(id: $environmentId) {
    applied {
      sources(after: $after, filter: $filter, first: $first) {
        edges {
          cursor
          node {
            accountId
            database
            children {
              ... on ExposureAppliedStateNestedNode {
                name
                uniqueId
                description
                url
              }
              ... on MetricDefinitionNestedNode {
                name
                description
                uniqueId
                resourceType
              }
              ... on ModelAppliedStateNestedNode {
                name
                description
                uniqueId
              }
            }
            description
            fqn
            freshness {
              freshnessChecked
              freshnessJobDefinitionId
              freshnessRunGeneratedAt
              freshnessRunId
              freshnessStatus
              maxLoadedAt
              maxLoadedAtTimeAgoInS
              snapshottedAt
            }
            identifier
            loader
            meta
            name
            projectId
            resourceType
            schema
            sourceDescription
            sourceName
            tags
            uniqueId
          }
        }
        pageInfo {
          endCursor
          hasNextPage
          hasPreviousPage
          startCursor
        }
        totalCount
      }
    }
  }
}
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "first": FIRST_N_RESULTS,
        "after": None,
        "filter": {
            "database": database,
            "freshnessChecked": freshness_checked,
            "schema": database_schema,
            "sourceNames": source_names,
            "tags": tags,
            "uniqueIds": unique_ids,
        },
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "environment", "applied", "sources", "edges"]
    )


@tool
def get_groups(
    environment_id: int = None,
    unique_ids: List[str] = None,
) -> List[Dict]:
    """Get a list of groups in a user's dbt Cloud project.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
        unique_ids (List[str], optional): Filter by unique IDs. Defaults to None.
    """
    client = get_client()
    query = """
query Definition($environmentId: BigInt!, $after: String, $filter: GroupFilter, $first: Int) {
  environment(id: $environmentId) {
    definition {
      groups(after: $after, filter: $filter, first: $first) {
        pageInfo {
          endCursor
          hasNextPage
          hasPreviousPage
          startCursor
        }
        totalCount
        edges {
          node {
            accountId
            description
            environmentId
            meta
            modelCount
            name
            ownerEmail
            ownerName
            packageName
            projectId
            runGeneratedAt
            resourceType
            uniqueId
            models {
              materializedType
              name
              description
              resourceType
              runGeneratedAt
              runId
              schema
              uniqueId
              database
            }
          }
        }
      }
    }
  }
}
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "first": FIRST_N_RESULTS,
        "after": None,
        "filter": {
            "uniqueIds": unique_ids,
        },
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "environment", "definition", "groups", "edges"]
    )


@tool
def get_semantic_models(
    environment_id: int = None,
    unique_ids: List[str] = None,
    database: str = None,
    database_schema: str = None,
    tags: List[str] = None,
    identifier: str = None,
) -> List[Dict]:
    """Get a list of semantic models in a user's dbt Cloud project, which consist of
    entities, measures, and dimensions.  Also, get an understanding of what models and
    sources feed into those semantic models and what metrics are created from the
    measures within the semantic model.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
        unique_ids (List[str], optional): Filter by unique IDs. Defaults to None.
        database (str, optional): Filter by database. Defaults to None.
        database_schema (str, optional): Filter by schema. Defaults to None.
        tags (List[str], optional): Filter by tags. Defaults to None.
        identifier (str, optional): Filter by identifier. Defaults to None.
    """
    client = get_client()
    query = """
query Definition($environmentId: BigInt!, $after: String, $filter: GenericMaterializedFilter, $first: Int) {
  environment(id: $environmentId) {
    definition {
      semanticModels(after: $after, filter: $filter, first: $first) {
        pageInfo {
          endCursor
          hasNextPage
          hasPreviousPage
          startCursor
        }
        totalCount
        edges {
          node {
            ancestors {
              ... on ExternalModelNode {
                name
                resourceType
                description
                database
                schema
                uniqueId
              }
              ... on ModelDefinitionNestedNode {
                database
                description
                group
                name
                resourceType
                schema
                uniqueId
              }
              ... on SnapshotDefinitionNestedNode {
                database
                name
                description
                schema
                uniqueId
              }
              ... on SourceDefinitionNestedNode {
                description
                database
                name
                resourceType
                schema
                sourceName
                sourceDescription
                uniqueId
              }
            }
            children {
              ... on MetricDefinitionNestedNode {
                description
                filter
                formula
                group
                name
                resourceType
                type
                typeParams
                uniqueId
              }
            }
            description
            dimensions {
              description
              name
              type
            }
            entities {
              description
              name
              type
            }
            measures {
              agg
              createMetric
              description
              expr
              name
            }
            name
            resourceType
            tags
            uniqueId
          }
        }
      }
    }
  }
}
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "first": FIRST_N_RESULTS,
        "after": None,
        "filter": {
            "database": database,
            "schema": database_schema,
            "tags": tags,
            "uniqueIds": unique_ids,
            "identifier": identifier,
        },
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "environment", "definition", "semanticModels", "edges"]
    )


@tool
def get_metrics(
    unique_ids: List[str],
    *,
    environment_id: int = None,
    database: str = None,
    database_schema: str = None,
    tags: List[str] = None,
    identifier: str = None,
) -> List[Dict]:
    """Get a list of metrics in a user's dbt Cloud project.

    Args:
        unique_ids (List[str], required): Filter by unique IDs.
        environment_id (int, optional): Environment ID. Defaults to None.
        database (str, optional): Filter by database. Defaults to None.
        database_schema (str, optional): Filter by schema. Defaults to None.
        tags (List[str], optional): Filter by tags. Defaults to None.
        identifier (str, optional): Filter by identifier. Defaults to None.
    """
    client = get_client()
    query = """
query Definition($environmentId: BigInt!, $after: String, $filter: GenericMaterializedFilter, $first: Int) {
  environment(id: $environmentId) {
    definition {
      metrics(after: $after, filter: $filter, first: $first) {
        pageInfo {
          endCursor
          hasNextPage
          hasPreviousPage
          startCursor
        }
        totalCount
        edges {
          node {
            ancestors {
              description
              name
              resourceType
              uniqueId
            }
            children {
              description
              name
              resourceType
              uniqueId
            }
            description
            filter
            formula
            group
            name
            meta
            resourceType
            type
            uniqueId
            tags
          }
        }
      }
    }
  }
}
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "first": FIRST_N_RESULTS,
        "after": None,
        "filter": {
            "database": database,
            "schema": database_schema,
            "tags": tags,
            "uniqueIds": unique_ids,
            "identifier": identifier,
        },
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "environment", "definition", "metrics", "edges"]
    )


@tool
def get_most_queried_resources(
    environment_id: int = None,
    start: str = None,
    end: str = None,
    limit: int = 5,
    resource_type: Literal["model", "source"] = "model",
) -> List[Dict]:
    """Get a list of the most queried resources in a user's dbt Cloud project.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
        start (str, optional): Start date in the format YYYY-MM-DD. Defaults to None.
        end (str, optional): End date in the format YYYY-MM-DD. Defaults to None.
        limit (int, optional): Number of resources to return. Defaults to 5.
        resource_type (Literal["model", "source"], optional): Resource type to filter by.
            Defaults to "model".
    """
    client = get_client()
    query = """
    query MostQueriedResources($end: Date!, $start: Date!, $environmentId: BigInt!, $limit: Int, $resourceType: [MostQueriedResourceType!]!) {
        performance(environmentId: $environmentId) {
            mostQueriedResources(end: $end, start: $start, limit: $limit, resourceType: $resourceType) {
            totalCount
            uniqueId
            }
        }
    }
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "start": start or (datetime.now() - timedelta(months=1)).strftime("%Y-%m-%d"),
        "end": end or datetime.now().strftime("%Y-%m-%d"),
        "limit": limit,
        "resourceType": [resource_type],
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "performance", "mostQueriedResources"]
    )


@tool
def get_resource_query_history(
    unique_id: str,
    *,
    environment_id: int = None,
    start: str = None,
    end: str = None,
) -> List[Dict]:
    """Get the query history for a given resource in a user's dbt project.

    Args:
        unique_id (str): Unique ID of the resource.  You may have to use another tool
            to get the unique_id of the resource (model or source) depending on what the
            user provides (they generally don't know what the unique ID is).
        environment_id (int, optional): Environment ID. Defaults to None.
        start (str, optional): Start date in the format YYYY-MM-DD. Defaults to None.
        end (str, optional): End date in the format YYYY-MM-DD. Defaults to None.
    """
    client = get_client()
    query = """
    query ResourceQueryHistory($environmentId: BigInt!, $end: Date!, $uniqueId: String!, $start: Date!) {
        performance(environmentId: $environmentId) {
            resourceQueryHistory(end: $end, uniqueId: $uniqueId, start: $start) {
                date
                totalCount
            }
        }
    }
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "uniqueId": unique_id,
        "start": start or (datetime.now() - timedelta(months=1)).strftime("%Y-%m-%d"),
        "end": end or datetime.now().strftime("%Y-%m-%d"),
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "performance", "resourceQueryHistory"]
    )


@tool
def get_resources(
    environment_id: int = None,
    resource_types: List[
        Literal[
            "Model",
            "Source",
            "Snapshot",
            "Test",
            "Seed",
            "Exposure",
            "Metric",
            "SemanticModel",
            "Macro",
        ]
    ] = ["Model"],
):
    """Get a list of resources in a user's dbt Cloud project.

    IMPORTANT:
        This tool should be used to find the unique_ids of resources to use in other
        tools.

    Args:
        environment_id (int, optional): Environment ID. Defaults to None.
        unique_ids (List[str], optional): Filter by unique IDs. Defaults to None.
        tags (List[str], optional): Filter by tags. Defaults to None.
    """
    client = get_client()
    query = """
query Resources($filter: DefinitionResourcesFilter!, $environmentId: BigInt!, $after: String, $first: Int) {
  environment(id: $environmentId) {
    definition {
      resources(filter: $filter, after: $after, first: $first) {
        pageInfo {
          endCursor
          hasNextPage
          hasPreviousPage
          startCursor
        }
        totalCount
        edges {
          node {
            description
            name
            resourceType
            tags
            uniqueId
          }
        }
      }
    }
  }
}
    """
    variables = {
        "environmentId": int(environment_id or os.environ["DBT_CLOUD_ENVIRONMENT_ID"]),
        "first": FIRST_N_RESULTS,
        "after": None,
        "filter": {
            "types": resource_types,
        },
    }
    response = client.metadata.query(query, variables)
    return _extract_nested_edges(
        response, ["data", "environment", "definition", "resources", "edges"]
    )


discovery_api_tools = [
    # get_consumer_projects,
    get_exposures,
    get_groups,
    get_longest_executed_models,
    get_metrics,
    get_model_performance_history,
    get_models,
    get_most_executed_models,
    get_most_failed_models,
    get_most_queried_resources,
    get_project_tags,
    get_recent_resource_changes,
    get_resource_counts,
    get_resource_query_history,
    get_resources,
    get_semantic_models,
    get_sources,
]
