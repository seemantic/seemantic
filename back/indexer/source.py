from abc import abstractmethod
from collections.abc import AsyncGenerator
from io import BytesIO

from pydantic import BaseModel


class UpsertEvent(BaseModel, arbitrary_types_allowed=True):
    uri: str
    content: BytesIO


class DeleteEvent(BaseModel):
    uri: str


DocumentEvent = UpsertEvent | DeleteEvent


class Source:
    """interface adapted to S3 / MinIO source for now"""

    @abstractmethod
    async def all_uris(self) -> list[str]: ...

    @abstractmethod
    def listen(self) -> AsyncGenerator[DocumentEvent]: ...
