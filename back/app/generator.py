from collections.abc import AsyncGenerator
from typing import Literal, TypedDict, cast

from litellm import CustomStreamWrapper, acompletion  # type: ignore[reportUnknownVariableType]
from pydantic import BaseModel

from app.search_engine import SearchResult


class GeneratorSettings(BaseModel, frozen=True):
    litellm_model: str


def on_result_context(search_result: SearchResult) -> str:
    chunks = [search_result.parsed_document[c.chunk] for c in search_result.chunks]

    chunks_str = ">>> \n".join(chunks)

    return f"""
    __Document {search_result.db_document.uri}__:

    {chunks_str}
    """


def all_results_context(search_results: list[SearchResult]) -> str:
    return "\n\n".join([on_result_context(r) for r in search_results])


class ChatMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class Generator:
    settings: GeneratorSettings
    litellm_api_key: str

    def __init__(self, settings: GeneratorSettings, litellm_api_key: str) -> None:
        self.settings = settings
        self.litellm_api_key = litellm_api_key

    async def generate(self, messages: list[ChatMessage]) -> AsyncGenerator[str, None]:

        response = await acompletion(self.settings.litellm_model, messages=messages, stream=True, api_key=self.litellm_api_key)
        stream_response: CustomStreamWrapper = cast("CustomStreamWrapper", response)

        async for chunk in stream_response:
            chunk_content = chunk.choices[0].delta.content # type: ignore[reportunkownMemberType]
            if isinstance(chunk_content, str):
                yield chunk_content

    def get_user_message(self, user_query: str, search_result: list[SearchResult]) -> ChatMessage:
        prompt = f"""
        Context information is below.
        ---------------------
        {all_results_context(search_result)}
        ---------------------
        Given the context infor/fixmation and not prior knowledge, answer the query.
        Query: {user_query}
        Answer:
        """
        return ChatMessage(role="user", content=prompt)
