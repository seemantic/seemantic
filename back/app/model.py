from pydantic import BaseModel


class DocumentSnippet(BaseModel):
    relative_path: str  # relative filepath within a source
