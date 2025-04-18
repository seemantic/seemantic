from collections.abc import AsyncGenerator

from mistralai import Mistral

from app.search_engine import SearchResult


def on_result_context(search_result: SearchResult) -> str:
    chunks = [search_result.parsed_document[c.chunk] for c in search_result.chunks]

    chunks_str = ">>> \n".join(chunks)

    return f"""
    __Document {search_result.db_document.uri}__:

    {chunks_str}
    """


def all_results_context(search_results: list[SearchResult]) -> str:
    return "\n\n".join([on_result_context(r) for r in search_results])


class Generator:
    mistral_client: Mistral
    model = "mistral-small-latest"

    def __init__(self, mistral_api_key: str) -> None:
        self.mistral_client = Mistral(api_key=mistral_api_key)

    async def generate(self, user_query: str, search_result: list[SearchResult]) -> AsyncGenerator[str, None]:
        prompt = f"""
        Context information is below.
        ---------------------
        {all_results_context(search_result)}
        ---------------------
        Given the context infor/fixmation and not prior knowledge, answer the query.
        Query: {user_query}
        Answer:
        """

        stream = await self.mistral_client.chat.stream_async(
            model=self.model,
            stream=True,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
        async for chunk in stream:
            choices = chunk.data.choices
            if choices:
                chunk_content = choices[0].delta.content
                if chunk_content is not None and isinstance(chunk_content, str):
                    yield chunk_content
