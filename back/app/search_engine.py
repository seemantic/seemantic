from copy import deepcopy
from pydantic import BaseModel

from common.document import Chunk
from common.db_service import DbService
from common.embedding_service import EmbeddingService
from common.vector_db import ChunkResult, ParsedDocumentResult, VectorDB


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


    def merge_chunks(self, doc_result: ParsedDocumentResult) -> ParsedDocumentResult:
        atomic_chunks = doc_result.chunk_results
        sorted_chunks = sorted(atomic_chunks, key=lambda chunk: chunk.chunk.start_index_in_doc)
        max_interval_for_merge = 50

        merged_chunks: list[ChunkResult] = []
        current_merged_chunk: ChunkResult = deepcopy(sorted_chunks[0])
        for chunk in sorted_chunks[1:]:
            if chunk.chunk.start_index_in_doc - current_merged_chunk.chunk.end_index_in_doc <= max_interval_for_merge:
                current_merged_chunk.distance = min(current_merged_chunk.distance, chunk.distance)
                current_merged_chunk.chunk.end_index_in_doc = max(chunk.chunk.end_index_in_doc, current_merged_chunk.chunk.end_index_in_doc)
            else:
                merged_chunks.append(current_merged_chunk)
                current_merged_chunk = deepcopy(chunk)

        merged_chunks.append(current_merged_chunk)
        return ParsedDocumentResult(parsed_document=doc_result.parsed_document, chunk_results=merged_chunks)




    async def search(self, query: str) -> list[SearchResult]:
        embedding = await self.embedding_service.embed_query(query)
        parsed_doc_results = await self.vector_db.query(embedding.embedding, 10)
        parsed_hashes = [result.parsed_document.hash for result in parsed_doc_results]
        hash_to_doc = await self.db.get_documents_from_indexed_parsed_hashes(parsed_hashes)
        # keep only results from documents in db
        parsed_doc_results = [result for result in parsed_doc_results if result.parsed_document.hash in hash_to_doc]
        # merge chunks
        parsed_doc_results = [self.merge_chunks(result) for result in parsed_doc_results]

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
