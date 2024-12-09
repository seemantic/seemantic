from uuid import UUID

from pydantic import BaseModel


class DocumentSnippet(BaseModel):
    relative_path: str  # relative filepath within a source, remains the same as document is modified
    permanent_doc_id: UUID  # uuid of the document, remains the same as document is modified, renamed, moved.
    parsed_doc_sha256: str  # hash of the parsed document content


class Document(BaseModel):
    document_snippet: DocumentSnippet
    markdown_content: str
