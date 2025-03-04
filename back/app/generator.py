from app.search_engine import SearchResult
from mistralai import Mistral


def on_result_context(search_result: SearchResult) -> str:
    chunks = [search_result.parsed_document[c.chunk] for c in search_result.chunks]

    chunks_str = '>>> \n'.join(chunks)

    return f"""
    __Document {search_result.db_document.uri}__:

    {chunks_str}
    """

def all_results_context(search_results: list[SearchResult]) -> str:

    return '\n\n'.join([on_result_context(r) for r in search_results])


class Generator:

    mistral_client: Mistral
    model = "mistral-small-latest"

    def __init__(self, mistral_api_key: str) -> None:
        self.mistral_client = Mistral(api_key=mistral_api_key)


    def generate(self, user_query:str, search_result: list[SearchResult]) -> str:


        prompt = f"""
        Context information is below.
        ---------------------
        {all_results_context(search_result)}
        ---------------------
        Given the context information and not prior knowledge, answer the query.
        Query: {user_query}
        Answer:
        """

        chat_response = self.mistral_client.chat.complete(
            model= self.model,
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

        choices = chat_response.choices
        if not choices:
            raise ValueError("No choices in response")
        
        content = choices[0].message.content

        if not content:
            raise ValueError("No content in response") 
        
        if isinstance(content, str):
            return content
        else:
            raise ValueError("Content is not a string")

