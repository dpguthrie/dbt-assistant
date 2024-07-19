# third party
from langchain_core.output_parsers import PydanticOutputParser

# first party
from dbt_assistant.tools.pydantic import Query

query_parser = PydanticOutputParser(pydantic_object=Query)


__all__ = ["query_parser"]
