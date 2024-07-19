# third party
from langchain.tools.retriever import create_retriever_tool

# first party
from dbt_assistant.retrievers.dbt_hub_retriever import DbtHubRetriever

INDEX_NAME = "dbt-hub"

docsearch = DbtHubRetriever().from_pinecone(INDEX_NAME)
retriever = docsearch.as_retriever()
dbt_hub_retriever_tool = create_retriever_tool(
    retriever,
    "dbt_hub_package_search",
    "Search for dbt Hub Packages.  Packages within dbt are a collection of macros, "
    "models, tests, and other resources that can be installed within your own dbt "
    "project.  This tool allows you to search for packages within dbt Hub. "
    "When returning data, always be sure to return the name of the package and "
    "then provide the relevant content for the user to consume. But the package name "
    "is incredibly important.",
)
