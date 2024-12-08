from infinity_emb import AsyncEngineArray, EngineArgs


class Embedder:

    engines = AsyncEngineArray.from_args(
        [
            EngineArgs(
                model_name_or_path="jinaai/jina-embeddings-v3",
                # model_name_or_path="michaelfeil/bge-small-en-v1.5",
                #engine="optimum",
                # embedding_dtype="float32",
                # dtype="auto",
            )
        ]
    )

    async def embed_text(self, sentences: list[str]):
        print(f"start embedding")
        async with self.engines[0] as engine:
            
            embeddings, usage = await engine.embed(sentences=sentences)
        return embeddings
