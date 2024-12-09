from uuid import UUID

from pydantic import BaseModel

from app.model import Document


class Passage(BaseModel):
    start_index_in_parsed_doc: int
    end_index_in_parsed_doc: int


class SearchResult(BaseModel):
    document: Document
    passages: list[Passage]


class SearchEngine:

    def index(self, documents: list[Document]) -> None:
        """
        add or update (if same permanent_doc_id but different parsed_doc_sha256)
        """
        raise NotImplementedError

    def remove_from_index(self, permanent_doc_ids: list[UUID]) -> None:
        raise NotImplementedError

    def search(self, query: str) -> list[SearchResult]:
        # 1. embed query

        raise NotImplementedError
