from http import HTTPStatus
from typing import Any, Final, Literal

import httpx

from common.document import Chunk, EmbeddedChunk, Embedding, ParsedDocument

type DistanceMetric = Literal["L2", "cosine", "dot"]


class EmbeddingService:

    _url: Final[str] = "https://api.jina.ai/v1/embeddings"
    _headers: Final[dict[str, str]]
    _max_chars: Final[int] = 15000  # heuristic because max is 8192 tokens

    def __init__(self, token: str) -> None:
        self._headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    async def _embed(self, task: str, content: list[str], *, late_chunking: bool) -> list[Embedding]:
        data: dict[str, Any] = {
            "model": "jina-embeddings-v3",
            "task": task,
            "late_chunking": late_chunking,
            "dimensions": 1024,
            "embedding_type": "float",
            "input": content,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self._url, headers=self._headers, json=data, timeout=60)

        if response.status_code != HTTPStatus.OK:
            message = f"Error embedding passage: {response.status_code} - {response.text}"
            raise ValueError(message)
        json = response.json()
        embeddings = [Embedding(embedding=embedding["embedding"]) for embedding in json["data"]]
        return embeddings

    async def embed_document(self, document: ParsedDocument, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        """
        embed contiguous passages from a single document
        Nb: for now the number of tokens is limited to 8192 tokens ot it will crash.
        """

        chunk_groups: list[list[Chunk]] = []
        current_group: list[Chunk] = []
        start_index_current_group = 0
        for chunk in chunks:
            if chunk.end_index_in_doc - start_index_current_group > self._max_chars:
                chunk_groups.append(current_group)
                current_group = [chunk]
                start_index_current_group = chunk.start_index_in_doc
            else:
                current_group.append(chunk)
        # add the last group
        if current_group:
            chunk_groups.append(current_group)

        results: list[EmbeddedChunk] = []
        for group in chunk_groups:
            chunk_contents = [document[chunk] for chunk in group]
            embeddings = await self._embed("retrieval.passage", chunk_contents, late_chunking=False)
            embedded_chunks = [
                EmbeddedChunk(chunk=chunk, embedding=embedding)
                for chunk, embedding in zip(group, embeddings, strict=True)
            ]
            results.extend(embedded_chunks)

        return results

    async def embed_query(self, query: str) -> Embedding:

        embeddings = await self._embed("retrieval.query", [query], late_chunking=False)
        embedding = embeddings[0]
        return embedding

    def distance_metric(self) -> DistanceMetric:
        return "cosine"
