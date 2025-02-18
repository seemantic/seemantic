from pydantic import BaseModel

from app.prompt_builder import PromptBuilder
from common.db_service import DbDocument, DbService
from common.document import ParsedDocument
from common.embedding_service import EmbeddingService
from common.vector_db import ChunkResult, VectorDB


class SearchResult(BaseModel):
    parsed_document: ParsedDocument
    db_document: DbDocument
    chunks: list[ChunkResult]


class SearchEngine:

    embedding_service: EmbeddingService
    vector_db: VectorDB
    db: DbService

    def __init__(self, embedding_service: EmbeddingService, vector_db: VectorDB, db: DbService) -> None:
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.db = db
        self.prompt_builder = PromptBuilder()

    async def search(self, query: str) -> list[SearchResult]:
        embedding = await self.embedding_service.embed_query(query)
        parsed_doc_results = await self.vector_db.query(embedding.embedding, 10)
        parsed_hashes = [result.parsed_document.hash for result in parsed_doc_results]
        hash_to_doc = await self.db.get_documents_from_indexed_parsed_hashes(parsed_hashes)
        # keep only results from documents in db
        parsed_doc_results = [result for result in parsed_doc_results if result.parsed_document.hash in hash_to_doc]

        search_results: list[SearchResult] = []
        for result in parsed_doc_results:
            db_doc = hash_to_doc.get(result.parsed_document.hash)
            extended = self.prompt_builder.merge_extend_passages(result.parsed_document, result.chunk_results)

            if db_doc:
                search_results.append(
                    SearchResult(
                        parsed_document=result.parsed_document,
                        db_document=db_doc,
                        chunks=extended,
                    ),
                )

        return search_results
