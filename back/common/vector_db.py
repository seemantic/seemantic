# ruff: noqa: ERA001

from pydantic import BaseModel

from common.document import Chunk, EmbeddedChunk, ParsedDocument


class ChunkResult(BaseModel):
    chunk: Chunk
    score: float


class DocumentResult(BaseModel):
    parsed_document: ParsedDocument
    chunk_results: list[ChunkResult]


class VectorDB:

    def __init__(self) -> None:
        pass

    def query(self, vector: list[float]) -> list[DocumentResult]:
        raise NotImplementedError

    def index(self, document: ParsedDocument, chunks: list[EmbeddedChunk]) -> None:
        raise NotImplementedError
