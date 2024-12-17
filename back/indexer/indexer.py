import logging

from indexer.sources.seemantic_drive import SeemanticDriveSource

from indexer.settings import get_settings


class Indexer:

    async def start(self) -> None:

        settings = get_settings()

        minio_source = SeemanticDriveSource(settings=settings.minio)

        async for doc_event in minio_source.listen():
            logging.info(doc_event)
            raise NotImplementedError("start_continuous_indexing")
