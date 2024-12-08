from app.embedder import Embedder
import pytest 

@pytest.mark.asyncio
async def test_embedder():
    embedder = Embedder()
    embeddings = await embedder.embed_text(["hello", "world"])
    print(embeddings)
