from abc import abstractmethod
from collections.abc import AsyncGenerator
from datetime import datetime
from io import BytesIO

from pydantic import BaseModel


class SourceDocumentReference(BaseModel):
    uri: str
    source_version_id: str | None


class SourceUpsertEvent(BaseModel):
    doc_ref: SourceDocumentReference


class SourceDeleteEvent(BaseModel):
    uri: str


SourceEvent = SourceUpsertEvent | SourceDeleteEvent


class SourceDocument(BaseModel, arbitrary_types_allowed=True):
    doc_ref: SourceDocumentReference
    content: BytesIO
    crawling_datetime: datetime
    filetype: str | None



class Source:
    """interface adapted to S3 / MinIO source for now"""

    @abstractmethod
    async def all_doc_refs(self) -> list[SourceDocumentReference]: ...

    @abstractmethod
    def listen(self) -> AsyncGenerator[SourceEvent]: ...

    @abstractmethod
    async def get_document(self, uri: str) -> SourceDocument | None: ...
