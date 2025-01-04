from common.embedding_service import EmbeddingService


async def test_embed_query() -> None:

    embedding_service = EmbeddingService("token")

    _ = await embedding_service.embed_query("query")
