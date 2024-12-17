import asyncio
import logging
from collections.abc import AsyncGenerator

from common.minio_service import MinioService
from indexer.settings import MinioSettings
from indexer.source import DeleteEvent, DocumentEvent, Source, UpsertEvent


class SeemanticDriveSource(Source):

    _settings: MinioSettings
    prefix = "seemantic_drive/"

    def __init__(self, settings: MinioSettings) -> None:
        self._minio_service = MinioService(settings=settings)

    async def all_uris(self) -> list[str]:
        return self._minio_service.get_all_documents(prefix=self.prefix)

    def listen(self) -> AsyncGenerator[DocumentEvent]:

        async def generator() -> AsyncGenerator[DocumentEvent]:
            for event in self._minio_service.listen_notifications(prefix=self.prefix):
                await asyncio.sleep(0)
                if event.event_type == "put":
                    content = self._minio_service.get_document(event.key)
                    if content:
                        yield UpsertEvent(uri=event.key, content=content)
                    else:
                        logging.warning(f"File {event.key} missing when calling get_document")
                elif event.event_type == "delete":
                    yield DeleteEvent(uri=event.key)

        return generator()
