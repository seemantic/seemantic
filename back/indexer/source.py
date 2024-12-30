from abc import abstractmethod
from collections.abc import AsyncGenerator
from datetime import datetime
from io import BytesIO

from common.document import SupportedFileType
from pydantic import BaseModel


class SourceUpsertEvent(BaseModel):
    uri: str


class SourceDeleteEvent(BaseModel):
    uri: str


SourceEvent = SourceUpsertEvent | SourceDeleteEvent


class SourceDocument(BaseModel, arbitrary_types_allowed=True):
    uri: str
    raw_content_hash: str
    content: BytesIO
    crawling_datetime: datetime
    filetype: SupportedFileType


class Source:
    """interface adapted to S3 / MinIO source for now"""

    @abstractmethod
    async def all_uris(self) -> list[str]: ...

    @abstractmethod
    def listen(self) -> AsyncGenerator[SourceEvent]: ...

    @abstractmethod
    async def get_document(self, uri: str) -> SourceDocument | None: ...
