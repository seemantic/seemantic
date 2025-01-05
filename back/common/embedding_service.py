from http import HTTPStatus
from typing import Final

import httpx

from common.document import Chunk, ParsedDocument


class EmbeddingService:

    _url: Final[str] = "https://api.jina.ai/v1/embeddings"
    _headers: Final[dict[str, str]]

    def __init__(self, token: str) -> None:
        self._headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    async def embed_document(self, document: ParsedDocument, chunks: list[Chunk]) -> list[list[float]]:
        """
        embed contiguous passages from a single document
        Nb: for now the number of tokens is limited to 8192 tokens ot it will crash.
        """
        chunk_contents = [document[chunk] for chunk in chunks]

        data = {
            "model": "jina-embeddings-v3",
            "task": "retrieval.passage",
            "late_chunking": True,
            "dimensions": 1024,
            "embedding_type": "float",
            "input": chunk_contents,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self._url, headers=self._headers, json=data)

        if response.status_code != HTTPStatus.OK:
            message = f"Error embedding passage: {response.status_code} - {response.text}"
            raise ValueError(message)
        json = response.json()
        embeddings = [embedding["embedding"] for embedding in json["data"]]
        return embeddings

    async def embed_query(self, query: str) -> list[float]:
        data = {
            "model": "jina-embeddings-v3",
            "task": "retrieval.query",
            "late_chunking": False,
            "dimensions": 1024,
            "embedding_type": "float",
            "input": [query],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self._url, headers=self._headers, json=data)

        if response.status_code != HTTPStatus.OK:
            message = f"Error embedding query: {response.status_code} - {response.text}"
            raise ValueError(message)
        json = response.json()
        embedding = json["data"][0]["embedding"]
        return embedding
