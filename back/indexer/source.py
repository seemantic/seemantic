from abc import abstractmethod
from collections.abc import AsyncGenerator
from datetime import datetime
from io import BytesIO

from pydantic import BaseModel


class SourceUpsertEvent(BaseModel):
    uri: str


class SourceDeleteEvent(BaseModel):
    uri: str


SourceEvent = SourceUpsertEvent | SourceDeleteEvent


class SourceDocument(BaseModel):
    uri: str
    raw_content_hash: str
    content: BytesIO
    crawling_datetime: datetime


class Source:
    """interface adapted to S3 / MinIO source for now"""

    @abstractmethod
    async def all_uris(self) -> list[str]: ...

    @abstractmethod
    def listen(self) -> AsyncGenerator[SourceEvent]: ...

    @abstractmethod
    async def get_document(self, uri: str) -> SourceDocument | None: ...
