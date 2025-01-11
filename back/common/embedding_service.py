from http import HTTPStatus
from typing import Final, Any

import httpx

from common.document import Chunk, EmbeddedChunk, Embedding, ParsedDocument


class EmbeddingService:

    _url: Final[str] = "https://api.jina.ai/v1/embeddings"
    _headers: Final[dict[str, str]]

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
            response = await client.post(self._url, headers=self._headers, json=data)

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
        chunk_contents = [document[chunk] for chunk in chunks]

        embeddings = await self._embed("retrieval.passage", chunk_contents, late_chunking=True)
        return [
            EmbeddedChunk(chunk=chunk, embedding=embedding)
            for chunk, embedding in zip(chunks, embeddings, strict=False)
        ]

    async def embed_query(self, query: str) -> Embedding:

        embeddings = await self._embed("retrieval.query", [query], late_chunking=False)
        embedding = embeddings[0]
        return embedding


