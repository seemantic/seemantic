import datetime as dt
import pathlib
from collections.abc import AsyncGenerator
from datetime import datetime

import filetype  # type: ignore[StubNotFound]

from common.minio_service import DeleteMinioEvent, MinioObjectContent, MinioService
from common.settings import MinioSettings
from indexer.source import (
    Source,
    SourceDeleteEvent,
    SourceDocument,
    SourceDocumentReference,
    SourceEvent,
    SourceUpsertEvent,
)


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

    async def all_doc_refs(self) -> list[SourceDocumentReference]:
        return [
            SourceDocumentReference(uri=self._without_prefix(object_name=obj.key), source_version_id=obj.etag)
            for obj in self._minio_service.get_all_documents(prefix=self.prefix)
        ]

    async def listen(self) -> AsyncGenerator[SourceEvent, None]:

        async for event in self._minio_service.async_listen_notifications(prefix=self.prefix):
            if isinstance(event, DeleteMinioEvent):
                yield SourceDeleteEvent(uri=self._without_prefix(event.key))
            else:
                yield SourceUpsertEvent(
                    doc_ref=SourceDocumentReference(
                        uri=self._without_prefix(event.object.key),
                        source_version_id=event.object.etag,
                    ),
                )

    async def get_document(self, uri: str) -> SourceDocument | None:
        object_content = self._minio_service.get_document(object_name=self._with_prefix(uri))

        if object_content:
            kind: str | None = self.get_extension(object_content, uri)
            object_content.content.seek(0)
            # check that kind is a supported file type
            return SourceDocument(
                doc_ref=SourceDocumentReference(uri=uri, source_version_id=object_content.object.etag),
                content=object_content.content,
                crawling_datetime=datetime.now(tz=dt.timezone.utc),
                filetype=kind,
            )
        return None

    def get_extension(self, object_content: MinioObjectContent, uri: str) -> str | None:
        kind: str | None = filetype.guess_extension(object_content.content.read(1024))  # type: ignore[Attribute]
        object_content.content.seek(0)
        if not kind:
            kind_with_dot_or_empty = pathlib.Path(uri).suffix
            kind = kind_with_dot_or_empty[1:] if kind_with_dot_or_empty else None
        return kind
