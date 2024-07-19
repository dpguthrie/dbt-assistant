# first party
import json
from typing import Iterator

# third party
from langchain_core.documents import Document

# first party
from dbt_assistant.loaders.base_loader import DbtBaseLoader

INTROSPECTION_QUERY = """
query IntrospectionQuery {
    __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
        ...FullType
    }
    directives {
        name
        description
        locations
        args(includeDeprecated: false) {
        ...InputValue
        }
    }
    }
}

fragment FullType on __Type {
    kind
    name
    description
    fields(includeDeprecated: false) {
    name
    description
    args(includeDeprecated: false) {
        ...InputValue
    }
    type {
        ...TypeRef
    }
    isDeprecated
    deprecationReason
    }
    inputFields(includeDeprecated: false) {
    ...InputValue
    }
    interfaces {
    ...TypeRef
    }
    enumValues(includeDeprecated: false) {
    name
    description
    isDeprecated
    deprecationReason
    }
    possibleTypes {
    ...TypeRef
    }
}

fragment InputValue on __InputValue {
    name
    description
    type { ...TypeRef }
    defaultValue
    isDeprecated
    deprecationReason
}

fragment TypeRef on __Type {
    kind
    name
    ofType {
    kind
    name
    ofType {
        kind
        name
        ofType {
        kind
        name
        ofType {
            kind
            name
            ofType {
            kind
            name
            ofType {
                kind
                name
                ofType {
                kind
                name
                }
            }
            }
        }
        }
    }
    }
}
"""


class DbtDiscoveryApiLoader(DbtBaseLoader):
    def _get_discovery_api_schema(self):
        query = INTROSPECTION_QUERY
        variables = {"operationName": "IntrospectionQuery"}
        json_response = self.client.metadata.query(query, variables)
        return json_response["data"]["__schema"]["types"]

    def lazy_load(self) -> Iterator:
        schema = self._get_discovery_api_schema()
        for item in schema:
            yield Document(page_content=json.dumps(item), metadata={})
