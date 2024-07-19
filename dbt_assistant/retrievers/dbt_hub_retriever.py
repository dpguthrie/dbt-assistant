# stdlib
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Union

# third party
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import PodSpec, ServerlessSpec
from pinecone.grpc import PineconeGRPC as Pinecone

# first party
from dbt_assistant.loaders.dbt_hub_loader import get_hub_documents

logging.basicConfig(
    level=logging.INFO,  # Set log level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define format
    datefmt="%Y-%m-%d %H:%M:%S",  # Optional: Customize date format
)
logger = logging.getLogger(__name__)


@dataclass
class PineconeIndexConfig:
    name: str
    dimension: int = 1536
    metric: str = "cosine"
    spec: Union[PodSpec, ServerlessSpec] = field(
        default_factory=lambda: ServerlessSpec(cloud="aws", region="us-east-1")
    )


class DbtHubRetriever:
    @classmethod
    def from_pinecone(cls, index_name: str, **index_kwargs):
        # TODO: Should be able to specify this
        embeddings = OpenAIEmbeddings()
        # Assumes that the PINECONE_API_KEY is in an environment variable
        pc = Pinecone()
        existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
        if index_name not in existing_indexes:
            index_config = PineconeIndexConfig(name=index_name, **index_kwargs)
            pc.create_index(**asdict(index_config))
            while not pc.describe_index(index_name).status["ready"]:
                time.sleep(1)

            docs = get_hub_documents()
            return PineconeVectorStore.from_documents(
                documents=docs,
                embedding=embeddings,
                index_name=index_name,
                batch_size=64,
                pool_threads=10,
            )

        return PineconeVectorStore.from_existing_index(index_name, embeddings)
