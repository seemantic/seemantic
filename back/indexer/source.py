from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Literal

from pydantic import BaseModel


class DocumentEvent(BaseModel):
    event_type: Literal["upsert", "delete"]
    uri: str
    content: bytes | None


class Source:
    """interface adapted to S3 / MinIO source for now"""

    @abstractmethod
    def all_uris(self) -> list[str]: ...

    @abstractmethod
    def listen(self) -> AsyncGenerator[DocumentEvent]: ...
