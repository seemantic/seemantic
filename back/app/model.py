from pydantic import BaseModel
from uuid import UUID


class DocumentSnippet(BaseModel):
    id: UUID
    relative_path: str  # relative filepath within a source