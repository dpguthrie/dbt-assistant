# stdlib
import hashlib
from abc import ABC, abstractmethod
from typing import List

# third party
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


class BaseRetriever(ABC):
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()

    @abstractmethod
    def create_vectorstore(self, documents: List[Document]):
        pass

    @abstractmethod
    def delete_vectorstore(self):
        pass

    @abstractmethod
    def get_vectorstore(self):
        pass

    @abstractmethod
    def update_vectorstore(self, documents: List[Document]):
        pass

    @abstractmethod
    def create_and_update_vectorstore(self, documents: List[Document]):
        pass

    def _generate_id_for_document(self, document: Document, keys_for_id: List[str]):
        try:
            repo = "-".join([document.metadata[key] for key in keys_for_id])
        except KeyError:
            raise ValueError(
                "Document must have all required metadata keys to generate an ID"
            )

        return hashlib.md5(repo.encode()).hexdigest()

    def _create_ids_for_documents(
        self, documents: List[Document], keys_for_id: List[str]
    ):
        return [
            self._generate_id_for_document(document, keys_for_id)
            for document in documents
        ]

    def _embed_documents(self, documents: List[Document]):
        return self.embeddings.embed_documents([doc.page_content for doc in documents])
