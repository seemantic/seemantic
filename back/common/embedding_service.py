from http import HTTPStatus
from typing import Final

import httpx


class EmbeddingService:

    _url: Final[str] = "https://api.jina.ai/v1/embeddings"
    _headers: Final[dict[str, str]]

    def __init__(self, token: str) -> None:
        self._headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    async def embed_passage(self, chunks: list[str]) -> list[list[float]]:
        """embed contiguous passages from a single document"""

        data = {
            "model": "jina-embeddings-v3",
            "task": "retrieval.passage",
            "late_chunking": True,
            "dimensions": 1024,
            "embedding_type": "float",
            "input": chunks,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self._url, headers=self._headers, json=data)

        if response.status_code != HTTPStatus.OK:
            message = f"Error embedding passage: {response.status_code} - {response.text}"
            raise ValueError(message)
        json = response.json()
        embeddings = [embedding["embedding"] for embedding in json["data"]]
        return embeddings
