from http import HTTPStatus
from typing import Any, Final, Literal

import httpx
from litellm import aembedding  # type: ignore[reportUnknownVariableType]

from common.document import Chunk, EmbeddedChunk, Embedding, ParsedDocument
from common.embedding_settings import EmbeddingSettings

type DistanceMetric = Literal["L2", "cosine", "dot"]
type EmbeddingTask = Literal["document", "query"]




#class EmbeddingSettings(BaseModel, frozen=True):
#    litellm_model: str
#    litellm_query_kwargs: dict[str, Any]
#    litellm_document_kwargs: dict[str, Any]


class EmbeddingService:

    settings: EmbeddingSettings
    litellm_api_key: str

    _url: Final[str] = "https://api.jina.ai/v1/embeddings"
    _headers: Final[dict[str, str]]
    _max_chars: Final[int] = 15000  # heuristic because max is 8192 tokens

    _token: str

    def __init__(self, settings: EmbeddingSettings, litellm_api_key: str) -> None:
        self.settings = settings
        self._headers = {"Content-Type": "application/json", "Authorization": f"Bearer {litellm_api_key}"}
        self.litellm_api_key = litellm_api_key

    async def _embed(self, task: EmbeddingTask, content: list[str], *, late_chunking: bool) -> list[Embedding]:
        data: dict[str, Any] = {
            "model": "jina-embeddings-v3",
            "task": "retrieval.passage" if task == "document" else "retrieval.query",
            "late_chunking": late_chunking,
            "dimensions": 1024,
            "embedding_type": "float",
            "input": content,
        }

        response_litellm =  await aembedding(
            model="jina_ai/jina-embeddings-v3",
            input=content,
            dimensions=1024,
            api_key=self.litellm_api_key,
            # kwargs
            **self.settings.document_kwargs_as_dict if task == "document" else self.settings.query_kwargs_as_dict,
        )
        vectors: list[dict[str,Any]] = response_litellm.data # type: ignore[reportUnknownVariableType]
        embeddings_litellm = [
            Embedding(embedding=vector["embedding"]) for vector in vectors # type: ignore[reportUnknownVariableType]
        ]


        async with httpx.AsyncClient() as client:
            response = await client.post(self._url, headers=self._headers, json=data, timeout=60)

        if response.status_code != HTTPStatus.OK:
            message = f"Error embedding passage: {response.status_code} - {response.text}"
            raise ValueError(message)
        json = response.json()
        embeddings = [Embedding(embedding=embedding["embedding"]) for embedding in json["data"]]

        # TODO HERE, remove check if litellm produces the same result
        # check if litellm and jina produce the same result
        for i, i_embedding in enumerate(embeddings):
            if not (i_embedding == embeddings_litellm[i]):
                raise ValueError(f"Litellm and Jina produce different results for the same input: {i}")


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
            embeddings = await self._embed("document", chunk_contents, late_chunking=False)
            embedded_chunks = [
                EmbeddedChunk(chunk=chunk, embedding=embedding)
                for chunk, embedding in zip(group, embeddings, strict=True)
            ]
            results.extend(embedded_chunks)

        return results

    async def embed_query(self, query: str) -> Embedding:

        embeddings = await self._embed("query", [query], late_chunking=False)
        embedding = embeddings[0]
        return embedding

    def distance_metric(self) -> DistanceMetric:
        return "cosine"
