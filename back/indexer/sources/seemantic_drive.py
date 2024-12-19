import asyncio
import datetime as dt
from collections.abc import AsyncGenerator
from datetime import datetime

from common.minio_service import MinioService
from common.utils import hash_file_content
from indexer.settings import MinioSettings
from indexer.source import Source, SourceDeleteEvent, SourceDocument, SourceEvent, SourceUpsertEvent


class SeemanticDriveSource(Source):

    _settings: MinioSettings
    prefix = "seemantic_drive/"

    def _without_prefix(self, object_name: str) -> str:
        assert object_name.startswith(self.prefix)
        return object_name[len(self.prefix) :]

    def _with_prefix(self, uri: str) -> str:
        return f"{self.prefix}{uri}"

    def __init__(self, settings: MinioSettings) -> None:
        self._minio_service = MinioService(settings=settings)

    async def all_uris(self) -> list[str]:
        return [
            self._without_prefix(object_name=doc_name)
            for doc_name in self._minio_service.get_all_documents(prefix=self.prefix)
        ]

    def listen(self) -> AsyncGenerator[SourceEvent]:

        async def generator() -> AsyncGenerator[SourceEvent]:
            for event in self._minio_service.listen_notifications(prefix=self.prefix):
                await asyncio.sleep(0)
                uri = self._without_prefix(event.key)
                if event.event_type == "put":
                    yield SourceUpsertEvent(uri=uri)
                elif event.event_type == "delete":
                    yield SourceDeleteEvent(uri=uri)

        return generator()

    async def get_document(self, uri: str) -> SourceDocument | None:
        content = self._minio_service.get_document(object_name=self._with_prefix(uri))
        if content:
            return SourceDocument(
                uri=uri,
                raw_content_hash=hash_file_content(content),
                content=content,
                crawling_datetime=datetime.now(tz=dt.timezone.utc),
            )
        return None
