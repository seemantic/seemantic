from typing import Any, Final, Literal

from litellm import aembedding  # type: ignore[reportUnknownVariableType]
from pydantic import BaseModel

from common.document import Chunk, EmbeddedChunk, Embedding, ParsedDocument
from common.settings_dict import SettingsDict

type DistanceMetric = Literal["L2", "cosine", "dot"]
type EmbeddingTask = Literal["document", "query"]


class EmbeddingSettings(BaseModel, frozen=True):
    litellm_model: str
    litellm_query_kwargs: SettingsDict
    litellm_document_kwargs: SettingsDict


class EmbeddingService:

    settings: EmbeddingSettings
    litellm_api_key: str

    _url: Final[str] = "https://api.jina.ai/v1/embeddings"
    _headers: Final[dict[str, str]]
    _max_chars: Final[int] = 15000  # heuristic because max is 8192 tokens

    _query_kwargs: dict[str, Any]
    _document_kwargs: dict[str, Any]

    def __init__(self, settings: EmbeddingSettings, litellm_api_key: str) -> None:
        self.settings = settings
        self._headers = {"Content-Type": "application/json", "Authorization": f"Bearer {litellm_api_key}"}
        self.litellm_api_key = litellm_api_key
        self._query_kwargs = dict(settings.litellm_query_kwargs)
        self._document_kwargs = dict(settings.litellm_document_kwargs)

    async def _embed(self, task: EmbeddingTask, content: list[str]) -> list[Embedding]:

        response_litellm = await aembedding(
            model="jina_ai/jina-embeddings-v3",
            input=content,
            dimensions=1024,
            api_key=self.litellm_api_key,
            # kwargs
            **(self._document_kwargs if task == "document" else self._query_kwargs),
        )
        vectors: list[dict[str, Any]] = response_litellm.data  # type: ignore[reportUnknownVariableType]
        embeddings_litellm = [
            Embedding(embedding=vector["embedding"]) for vector in vectors  # type: ignore[reportUnknownVariableType]
        ]

        return embeddings_litellm

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
            embeddings = await self._embed("document", chunk_contents)
            embedded_chunks = [
                EmbeddedChunk(chunk=chunk, embedding=embedding)
                for chunk, embedding in zip(group, embeddings, strict=True)
            ]
            results.extend(embedded_chunks)

        return results

    async def embed_query(self, query: str) -> Embedding:

        embeddings = await self._embed("query", [query])
        embedding = embeddings[0]
        return embedding

    def distance_metric(self) -> DistanceMetric:
        return "cosine"
