from pathlib import Path

from docling.document_converter import DocumentConverter  # type: ignore[StubNotFound]
from pydantic import BaseModel


class DocumentIdentifier(BaseModel):
    file_path: Path


class Document(BaseModel):
    markdown_content: str
    doc_id: DocumentIdentifier


class Parser:

    converter: DocumentConverter = DocumentConverter()

    def parse(self, file_path: Path) -> Document:
        result = self.converter.convert(file_path)
        docling_doc = result.document
        md = docling_doc.export_to_markdown()
        return Document(markdown_content=md, doc_id=DocumentIdentifier(file_path=file_path))
