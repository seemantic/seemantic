import logging

from indexer.settings import get_settings
from indexer.sources.minio import MinioSource


class Indexer:

    async def start(self) -> None:

        settings = get_settings()

        minio_source = MinioSource(settings=settings.minio)

        async for doc_event in minio_source.listen():
            logging.debug(doc_event)
            raise NotImplementedError("start_continuous_indexing")
