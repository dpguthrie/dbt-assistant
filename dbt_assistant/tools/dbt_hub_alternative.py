# stdlib
import os

# third party
if os.getenv("TAVILY_API_KEY", None) is not None:
    from langchain_community.tools.tavily_search import (
        TavilySearchResults as SearchTool,
    )

    kwargs = {
        "include_domains": ["hub.getdbt.com"],
        "include_images": True,
    }
else:
    from langchain_community.tools import DuckDuckGoSearchResults as SearchTool

    kwargs = {}

common_kwargs = {
    "max_results": 3,
    "name": "dbt_docs_search_tool",
    "description": """
    This tool searches for anything related to dbt's packages, which are all contained 
    at hub.getdbt.com.  Questions around dbt packages can be answered using this tool.
    """,
}

hub_tool_alternative = SearchTool(**kwargs, **common_kwargs)
