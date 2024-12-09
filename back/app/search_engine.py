from uuid import UUID

from pydantic import BaseModel

from app.model import Document


class Passage(BaseModel):
    start_index_in_doc: int
    end_index_in_doc: int


class SearchResult(BaseModel):
    document: Document
    passages: list[Passage]


class SearchEngine:

    def index(self, documents: list[Document]) -> None:
        """
        add or update the documents with the same permanent_doc_id but a different parsed_doc_id
        """
        raise NotImplementedError

    def remove_from_index(self, permanent_doc_ids: list[UUID]) -> None:
        raise NotImplementedError

    def search(self, query: str) -> list[SearchResult]:
        # 1. embed query

        raise NotImplementedError
