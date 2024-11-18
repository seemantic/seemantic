from pydantic import BaseModel
from uuid import UUID


class DocumentSnippet(BaseModel):
    id: UUID
    uri: str  # relative filepath within a source