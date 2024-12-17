from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Literal

from pydantic import BaseModel


class DocumentEvent(BaseModel):
    event_type: Literal["upsert", "delete"]
    uri: str
    content: bytes | None


class Source:

    @abstractmethod
    def start(self) -> AsyncGenerator[DocumentEvent]: ...
