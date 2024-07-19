# stdlib
from datetime import datetime, timedelta
from typing import Any, Literal, Optional, Union

# third party
from langchain_core.pydantic_v1 import BaseModel, Extra, root_validator
from langchain_core.utils import get_from_dict_or_env

FIRST_N_RESULTS = 500
DEFAULT_DAYS_AGO = 14
MAXIMUM_DAYS_AGO = 90


class DbtCloudApiWrapper(BaseModel):
    """Wrapper for dbt Cloud API."""

    dbt_cloud_environment_id: Optional[int] = None
    dbt_cloud_service_token: Optional[str] = None
    dbt_cloud_host: Optional[str] = "cloud.getdbt.com"
    client: Any

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    @root_validator(pre=True)
    def validate_environment(cls, values: dict) -> dict:
        """
        Validate that the environment is set up correctly and package exists in
        environment.
        """
        environment_id = get_from_dict_or_env(
            values, "dbt_cloud_environment_id", "DBT_CLOUD_ENVIRONMENT_ID"
        )
        service_token = get_from_dict_or_env(
            values, "dbt_cloud_service_token", "DBT_CLOUD_SERVICE_TOKEN"
        )
        host = get_from_dict_or_env(values, "dbt_cloud_host", "DBT_CLOUD_HOST")

        try:
            from dbtc import dbtCloudClient
        except ImportError:
            raise ImportError(
                "dbtc package is not installed.  "
                "Please install it with `pip install dbtc`."
            )

        client = dbtCloudClient(
            service_token=service_token, environment_id=environment_id, host=host
        )

        values["client"] = client
        values["dbt_cloud_environment_id"] = environment_id
        values["dbt_cloud_service_token"] = service_token
        values["dbt_cloud_host"] = host

        return values

    # Semantic Layer

    def _parse_semantic_layer_response(self, response: dict, key: str) -> list:
        """Parse a semantic layer response."""
        try:
            data = response.get("data", {}).get(key, [])
        except (KeyError, AttributeError):
            try:
                return [response["error"]]
            except KeyError:
                return []

        if not data:
            return [response.get("error", "No data found in the response.")]

        return data

    def list_dimensions(self, metrics=list[str]) -> list:
        """List all dimensions for a given list of metrics."""
        json_response = self.client.sl.list_dimensions(metrics)
        return self._parse_semantic_layer_response(json_response, "dimensions")

    def list_entities(self, metrics=list[str]) -> list:
        """List all entities for a given list of metrics."""
        json_response = self.client.sl.list_entities(metrics)
        return self._parse_semantic_layer_response(json_response, "entities")

    def list_measures(self, metrics=list[str]) -> list:
        """List all measures for a given list of metrics."""
        json_response = self.client.sl.list_measures(metrics)
        return self._parse_semantic_layer_response(json_response, "measures")

    def list_metrics(self) -> list:
        """List all metrics."""
        json_response = self.client.sl.list_metrics()
        return self._parse_semantic_layer_response(json_response, "metrics")

    def list_metrics_for_dimensions(self, dimensions=list[str]) -> list:
        """List all metrics for a given list of dimensions."""
        json_response = self.client.sl.list_metrics_for_dimensions(dimensions)
        return self._parse_semantic_layer_response(
            json_response, "metricsForDimensions"
        )

    def list_queryable_granularities(self, metrics: list[str]) -> list:
        """List all queryable granularities for a given list of metrics."""
        json_response = self.client.sl.list_queryable_granularities(metrics)
        return self._parse_semantic_layer_response(
            json_response, "queryableGranularities"
        )

    def list_saved_queries(self) -> list:
        """List all saved queries."""
        json_response = self.client.sl.list_saved_queries()
        return self._parse_semantic_layer_response(json_response, "savedQueries")

    def list_dimension_values(self, dimension: str) -> list:
        """List all values for a given dimension."""
        response = self.client.sl.list_dimension_values(dimension)
        if isinstance(response, str):
            return [response]

        return response

    def query_semantic_layer(
        self,
        metrics: list[str],
        *,
        group_by: list[str] = None,
        order_by: list[str] = None,
        limit: int = None,
        saved_query: str = None,
        grain: str = "DAY",
        output_format: Literal["pandas", "arrow", "list", "raw"] = "arrow",
    ) -> dict:
        """Query the dbt Cloud Semantic Layer.

        Important to note: If a saved_query is specified, it should be the only
        parameter passed in.  If other parameters are passed in, the saved_query
        will be ignored.
        """
        return self.client.sl.query_semantic_layer(
            metrics=metrics,
            group_by=group_by,
            order_by=order_by,
            limit=limit,
            saved_query=saved_query,
            grain=grain,
            output_format=output_format,
        ).dict()

    # Discovery API

    def _create_date_range(
        self, start_date: str = None, end_date: str = None
    ) -> tuple[str, str]:
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
        self,
        response: Union[list[dict], dict],
        keys: list[str],
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
                    return [{"error": error_message}]

            # If we've successfully navigated to 'edges' extend our list
            if isinstance(current, list):
                all_edges.extend(current)

        return all_edges

    def get_longest_executed_models(
        self,
        *,
        environment_id: int = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 5,
        job_limit: int = 5,
        job_id: int = None,
        order_by: Literal["AVG", "MAX"] = "MAX",
    ) -> list[dict]:
        """Get a list of the longest executed models for a given timeframe (defaults to
        the last 2 weeks) in a user's dbt Cloud project.

        Args:
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
        start_date, end_date = self._create_date_range(start_date, end_date)
        response = self.client.metadata.longest_executed_models(
            environment_id=environment_id or self.dbt_cloud_environment_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            job_limit=job_limit,
            job_id=job_id,
            order_by=order_by,
        )
        return self._extract_nested_edges(
            response, ["data", "performance", "longestExecutedModels"]
        )

    def get_model_execution_history(
        self,
        unique_id: str,
        *,
        start_date: str = None,
        end_date: str = None,
        environment_id: int = None,
    ) -> list[dict]:
        """Get the execution history (performance) for a given model in a user's dbt project.

        Args:
            unique_id (str): Unique ID of the model.
            start_date (str, optional): Start date in the format YYYY-MM-DD.
                Defaults to None.
            end_date (str, optional): End date in the format YYYY-MM-DD.
                Defaults to None.
            environment_id (int, optional): Environment ID. Defaults to None.
        """
        start_date, end_date = self._create_date_range(start_date, end_date)
        response = self.client.metadata.model_execution_history(
            unique_id=unique_id,
            start_date=start_date,
            end_date=end_date,
            environment_id=environment_id or self.dbt_cloud_environment_id,
        )
        return self._extract_nested_edges(
            response, ["data", "performance", "modelExecutionHistory"]
        )

    def get_most_executed_models(
        self,
        *,
        environment_id: int = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 5,
        job_limit: int = 5,
    ) -> list[dict]:
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
        start_date, end_date = self._create_date_range(start_date, end_date)
        response = self.client.metadata.most_executed_models(
            environment_id=environment_id or self.dbt_cloud_environment_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            job_limit=job_limit,
        )
        return self._extract_nested_edges(
            response, ["data", "performance", "mostExecutedModels"]
        )

    def get_most_failed_models(
        self,
        *,
        environment_id: int = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 5,
    ) -> list[dict]:
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
        start_date, end_date = self._create_date_range(start_date, end_date)
        response = self.client.metadata.most_failed_models(
            environment_id=environment_id or self.dbt_cloud_environment_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return self._extract_nested_edges(
            response, ["data", "performance", "mostFailedModels"]
        )

    def get_consumer_projects(self, *, environment_id: int = None) -> list[dict]:
        """
        Get a list of consumer projects in a user's dbt Cloud account.

        Args:
            environment_id (int, optional): Environment ID. Defaults to None.
        """
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
        variables = {"environmentId": environment_id or self.dbt_cloud_environment_id}
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response, ["data", "environment", "consumerProjects"]
        )

    def get_exposures(
        self,
        unique_ids: list[str],
        *,
        environment_id: int = None,
        exposure_type: str = None,
        tags: list[str] = None,
    ) -> list[dict]:
        """Get a list of exposures in a user's dbt Cloud account.

        Args:
            unique_ids (List[str], required): Filter by unique IDs.
            environment_id (int, optional): Environment ID. Defaults to None.
            exposure_type (str, optional): Filter by exposure type. Defaults to None.
            tags (List[str], optional): Filter by tags. Defaults to None.
        """
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
            "environmentId": environment_id or self.dbt_cloud_environment_id,
            "first": FIRST_N_RESULTS,
            "after": None,
            "filter": {
                "exposureType": exposure_type,
                "tags": tags,
                "uniqueIds": unique_ids,
            },
        }
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response, ["data", "environment", "applied", "exposures", "edges"]
        )

    def get_models(
        self,
        unique_ids: list[str],
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
        tags: list[str] = None,
    ) -> list[dict]:
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
            "environmentId": environment_id or self.dbt_cloud_environment_id,
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
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response, ["data", "environment", "applied", "models", "edges"]
        )

    def get_recent_resource_changes(
        self,
        *,
        environment_id: int = None,
        number_of_days: int = 7,
    ) -> list[dict]:
        """Get a list of recent resource changes in a user's dbt Cloud project.

        Args:
            environment_id (int, optional): Environment ID. Defaults to None.
            number_of_days (int, optional): Number of days to look back. Defaults to 7.
        """
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
            "environmentId": environment_id or self.dbt_cloud_environment_id,
            "first": FIRST_N_RESULTS,
            "after": None,
            "numDays": number_of_days,
        }
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response,
            ["data", "environment", "applied", "recentResourceChanges", "edges"],
        )

    def get_resource_counts(self, *, environment_id: int = None) -> dict:
        """Get a count of resources in a user's dbt Cloud project.

        Args:
            environment_id (int, optional): Environment ID. Defaults to None.
        """
        query = """
        query Environment($environmentId: BigInt!) {
        environment(id: $environmentId) {
            applied {
            resourceCounts
            }
        }
        }
        """
        variables = {"environmentId": environment_id or self.dbt_cloud_environment_id}
        response = self.client.metadata.query(query, variables)
        return response["data"]["environment"]["applied"]["resourceCounts"]

    def get_project_tags(self, *, environment_id: int = None) -> list[dict]:
        """Get a list of project tags in a user's dbt Cloud project.

        Args:
            environment_id (int, optional): Environment ID. Defaults to None.
        """
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
        variables = {"environmentId": environment_id or self.dbt_cloud_environment_id}
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response, ["data", "environment", "applied", "tags"]
        )

    def get_sources(
        self,
        unique_ids: list[str],
        *,
        environment_id: int = None,
        database: str = None,
        freshness_checked: bool = None,
        database_schema: str = None,
        source_names: list[str] = None,
        tags: list[str] = None,
    ) -> list[dict]:
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
            "environmentId": environment_id or self.dbt_cloud_environment_id,
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
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response, ["data", "environment", "applied", "sources", "edges"]
        )

    def get_groups(
        self,
        *,
        environment_id: int = None,
        unique_ids: list[str] = None,
    ) -> list[dict]:
        """Get a list of groups in a user's dbt Cloud project.

        Args:
            environment_id (int, optional): Environment ID. Defaults to None.
            unique_ids (List[str], optional): Filter by unique IDs. Defaults to None.
        """
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
            "environmentId": environment_id or self.dbt_cloud_environment_id,
            "first": FIRST_N_RESULTS,
            "after": None,
            "filter": {
                "uniqueIds": unique_ids,
            },
        }
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response, ["data", "environment", "definition", "groups", "edges"]
        )

    def get_most_queried_resources(
        self,
        *,
        environment_id: int = None,
        start: str = None,
        end: str = None,
        limit: int = 5,
        resource_type: Literal["model", "source"] = "model",
    ) -> list[dict]:
        """Get a list of the most queried resources in a user's dbt Cloud project.

        Args:
            environment_id (int, optional): Environment ID. Defaults to None.
            start (str, optional): Start date in the format YYYY-MM-DD. Defaults to None.
            end (str, optional): End date in the format YYYY-MM-DD. Defaults to None.
            limit (int, optional): Number of resources to return. Defaults to 5.
            resource_type (Literal["model", "source"], optional): Resource type to filter by.
                Defaults to "model".
        """
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
        start_date, end_date = self._create_date_range(start, end)
        variables = {
            "environmentId": environment_id or self.dbt_cloud_environment_id,
            "start": start_date,
            "end": end_date,
            "limit": limit,
            "resourceType": [resource_type],
        }
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response, ["data", "performance", "mostQueriedResources"]
        )

    def get_resource_query_history(
        self,
        unique_id: str,
        *,
        environment_id: int = None,
        start: str = None,
        end: str = None,
    ) -> list[dict]:
        """Get the query history for a given resource in a user's dbt project.

        Args:
            unique_id (str): Unique ID of the resource.  You may have to use another tool
                to get the unique_id of the resource (model or source) depending on what the
                user provides (they generally don't know what the unique ID is).
            environment_id (int, optional): Environment ID. Defaults to None.
            start (str, optional): Start date in the format YYYY-MM-DD. Defaults to None.
            end (str, optional): End date in the format YYYY-MM-DD. Defaults to None.
        """
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
        start_date, end_date = self._create_date_range(start, end)
        variables = {
            "environmentId": environment_id or self.dbt_cloud_environment_id,
            "uniqueId": unique_id,
            "start": start_date,
            "end": end_date,
        }
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response, ["data", "performance", "resourceQueryHistory"]
        )

    def get_resources(
        self,
        *,
        environment_id: int = None,
        unique_ids: list[str] = None,
        resource_types: list[
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
    ) -> list[dict]:
        """Get a list of resources in a user's dbt Cloud project.

        IMPORTANT:
            This tool should be used to find the unique_ids of resources to use in other
            tools.

        Args:
            environment_id (int, optional): Environment ID. Defaults to None.
            unique_ids (List[str], optional): Filter by unique IDs. Defaults to None.
            resource_types (List[Literal[...]], optional): Filter by resource types.
        """
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
            "environmentId": environment_id or self.dbt_cloud_environment_id,
            "first": FIRST_N_RESULTS,
            "after": None,
            "filter": {
                "types": resource_types,
                "uniqueIds": unique_ids,
            },
        }
        response = self.client.metadata.query(query, variables)
        return self._extract_nested_edges(
            response, ["data", "environment", "definition", "resources", "edges"]
        )

    def run(self, mode: str, **kwargs) -> str:
        if mode == "list_dimensions":
            return self.list_dimensions(**kwargs)
        elif mode == "list_entities":
            return self.list_entities(**kwargs)
        elif mode == "list_measures":
            return self.list_measures(**kwargs)
        elif mode == "list_metrics":
            return self.list_metrics()
        elif mode == "list_metrics_for_dimensions":
            return self.list_metrics_for_dimensions(**kwargs)
        elif mode == "list_queryable_granularities":
            return self.list_queryable_granularities(**kwargs)
        elif mode == "list_saved_queries":
            return self.list_saved_queries()
        elif mode == "list_dimension_values":
            return self.list_dimension_values(**kwargs)
        elif mode == "query_semantic_layer":
            return self.query_semantic_layer(**kwargs)
        elif mode == "get_longest_executed_models":
            return self.get_longest_executed_models(**kwargs)
        elif mode == "get_model_execution_history":
            return self.get_model_execution_history(**kwargs)
        elif mode == "get_most_executed_models":
            return self.get_most_executed_models(**kwargs)
        elif mode == "get_most_failed_models":
            return self.get_most_failed_models(**kwargs)
        elif mode == "get_consumer_projects":
            return self.get_consumer_projects(**kwargs)
        elif mode == "get_exposures":
            return self.get_exposures(**kwargs)
        elif mode == "get_models":
            return self.get_models(**kwargs)
        elif mode == "get_recent_resource_changes":
            return self.get_recent_resource_changes(**kwargs)
        elif mode == "get_resource_counts":
            return self.get_resource_counts(**kwargs)
        elif mode == "get_project_tags":
            return self.get_project_tags(**kwargs)
        elif mode == "get_sources":
            return self.get_sources(**kwargs)
        elif mode == "get_groups":
            return self.get_groups(**kwargs)
        elif mode == "get_most_queried_resources":
            return self.get_most_queried_resources(**kwargs)
        elif mode == "get_resource_query_history":
            return self.get_resource_query_history(**kwargs)
        elif mode == "get_resources":
            return self.get_resources(**kwargs)
        else:
            raise ValueError(f"Invalid mode: {mode}")
