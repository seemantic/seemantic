from pydantic import BaseModel

from common.db_service import DbService
from common.embedding_service import EmbeddingService
from common.vector_db import VectorDB


class SearchDocument(BaseModel):
    doc_uri: str


class Passage(BaseModel):
    start_index_in_parsed_doc: int
    end_index_in_parsed_doc: int
    content: str


class SearchResult(BaseModel):
    document: SearchDocument
    passages: list[Passage]


class SearchEngine:

    embedding_service: EmbeddingService
    vector_db: VectorDB
    db: DbService

    def __init__(self, embedding_service: EmbeddingService, vector_db: VectorDB, db: DbService) -> None:
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.db = db

    async def search(self, query: str) -> list[SearchResult]:
        embedding = await self.embedding_service.embed_query(query)

        parsed_doc_results = await self.vector_db.query(embedding.embedding, 10)

        parsed_hashes = [result.parsed_document.hash for result in parsed_doc_results]

        hash_to_doc = await self.db.get_documents_from_indexed_parsed_hashes(parsed_hashes)

        search_results: list[SearchResult] = []
        for result in parsed_doc_results:
            doc = hash_to_doc.get(result.parsed_document.hash)
            if doc:
                search_results.append(
                    SearchResult(
                        document=SearchDocument(doc_uri=doc.uri),
                        passages=[
                            Passage(
                                start_index_in_parsed_doc=passage.chunk.start_index_in_doc,
                                end_index_in_parsed_doc=passage.chunk.end_index_in_doc,
                                content=result.parsed_document[passage.chunk],
                            )
                            for passage in result.chunk_results
                        ],
                    ),
                )

        return search_results
