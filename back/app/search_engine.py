import logging

from pydantic import BaseModel

from app.prompt_builder import PromptBuilder
from common.db_service import DbDocument, DbService
from common.document import ParsedDocument
from common.embedding_service import EmbeddingService
from common.vector_db import ChunkResult, VectorDB

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    parsed_document: ParsedDocument
    db_document: DbDocument
    chunks: list[ChunkResult]


class SearchEngine:

    embedding_service: EmbeddingService
    vector_db: VectorDB
    db: DbService
    indexer_version: int
    prompt_builder: PromptBuilder

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_db: VectorDB,
        db: DbService,
        indexer_version: int,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.db = db
        self.indexer_version = indexer_version
        self.prompt_builder = PromptBuilder()

    async def search(self, query: str) -> list[SearchResult]:
        embedding = await self.embedding_service.embed_query(query)
        parsed_doc_results = await self.vector_db.query(embedding.embedding, 10)
        parsed_hashes = [result.parsed_document.hash for result in parsed_doc_results]
        hash_to_doc = await self.db.get_documents_from_indexed_parsed_hashes(parsed_hashes, self.indexer_version)
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

    async def get_document(self, uri: str) -> ParsedDocument | None:
        db_doc = await self.db.get_documents([uri], self.indexer_version)
        if uri not in db_doc:
            return None
        db_doc = db_doc[uri]
        if not db_doc.indexed_content:
            return None
        parsed_doc = await self.vector_db.get_document(db_doc.indexed_content.parsed_hash)
        if not parsed_doc:
            logger.warning(
                f"Inconsistent state: document {uri} is marked as indexed with parsed hash {db_doc.indexed_content.parsed_hash} but not found in vector db",
            )
            return None
        return parsed_doc
