from uuid import UUID

from pydantic import BaseModel


class DocumentSnippet(BaseModel):
    id: UUID
    relative_path: str  # relative filepath within a source
    content_sha256: str
