# stdlib
from typing import Iterator

# third party
from langchain_core.documents import Document

# first party
from dbt_assistant.loaders.base_loader import DbtBaseLoader


class DbtSemanticLoader(DbtBaseLoader):
    ADDITIONAL_METADATA_ATTRIBUTES = {
        "dimensions": ["description", "type", "expr", "label", "qualifiedName"],
        "measures": ["agg", "aggTimeDimension", "expr"],
        "entities": ["description", "expr", "role", "type"],
    }

    def __init__(
        self,
        environment_id: int,
        *,
        token: str = None,
        host: str = None,
    ):
        super().__init__(token=token, host=host)
        self.client.sl.environment_id = environment_id

    def _page_content(self, obj: dict) -> str:
        return f"Metric Name: {obj['name']}, Metric Label: {obj['label']}, Metric Description: {obj['description']}"

    def _page_metadata(self, obj: dict) -> dict:
        def list_contents_to_string(
            items: list[dict], *, name_attr: str = "name"
        ) -> str:
            all_items = []
            for item in items:
                ls = [f"Name: {item[name_attr]}"]
                for attr in self.ADDITIONAL_METADATA_ATTRIBUTES[key]:
                    if attr in item and item[attr] is not None:
                        ls.append(f"{attr}: {item[attr]}")
                all_items.append(", ".join(ls))
            return "; ".join([item for item in all_items])

        metadata = {
            "metric_type": obj["type"],
            "requires_metric_time": obj["requiresMetricTime"],
        }
        for key in self.ADDITIONAL_METADATA_ATTRIBUTES.keys():
            list_str = list_contents_to_string(obj[key])
            if list_str:
                metadata.update({key: list_str})

        return metadata

    def lazy_load(self) -> Iterator:
        response = self.client.sl.list_metrics()
        try:
            metrics = response["data"]["metrics"]
        except KeyError:
            raise ValueError("No metrics found in the response.")

        if not metrics:
            raise ValueError("No metrics found in the response.")

        for metric in metrics:
            yield Document(
                page_content=self._page_content(metric),
                metadata=self._page_metadata(metric),
            )
