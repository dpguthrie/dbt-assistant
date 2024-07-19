# stdlib
import os

# third party
if os.getenv("TAVILY_API_KEY", None) is not None:
    from langchain_community.tools.tavily_search import (
        TavilySearchResults as SearchTool,
    )

    kwargs = {
        "include_domains": [
            " docs.getdbt.com",
            " getdbt.com",
            " discourse.getdbt.com",
            " blog.getdbt.com",
        ],
        "include_images": True,
    }
else:
    from langchain_community.tools import DuckDuckGoSearchResults as SearchTool

    kwargs = {}

common_kwargs = {
    "max_results": 5,
    "name": "dbt_docs_search_tool",
    "description": """
    This tool searches anything related to dbt's documentation. The goal of this tool
    is to give the user answers to their question from content specifically retrieved 
    from any of these domains:  docs.getdbt.com, getdbt.com, discourse.getdbt.com, and 
    blog.getdbt.com.
    """,
}

docs_tool = SearchTool(**kwargs, **common_kwargs)
