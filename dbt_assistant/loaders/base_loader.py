# stdlib
import os
from typing import Iterator

# third party
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class DbtBaseLoader(BaseLoader):
    DEFAULT_HOST = "cloud.getdbt.com"

    def __init__(
        self,
        *,
        token: str = None,
        host: str = None,
        environment_id: int = None,
    ):
        try:
            from dbtc import dbtCloudClient
        except ImportError:
            raise ImportError(
                "You must install the dbtc package to use the DbtManifestLoader."
            )

        self.token = token or os.getenv("DBT_CLOUD_SERVICE_TOKEN", None)
        if self.token is None:
            raise ValueError("You must provide a token to use the DbtManifestLoader.")

        self.host = host or os.getenv("DBT_CLOUD_HOST", self.DEFAULT_HOST)
        self.environment_id = environment_id or os.getenv(
            "DBT_CLOUD_ENVIRONMENT_ID", None
        )
        self.client = dbtCloudClient(
            service_token=self.token, host=self.host, environment_id=self.environment_id
        )

    def lazy_load(self) -> Iterator[Document]:
        raise NotImplementedError
