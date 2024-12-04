from pathlib import Path

from docling.document_converter import ConversionResult, DocumentConverter  # type: ignore[StubNotFound]
from pydantic import BaseModel


class Document(BaseModel):
    markdown_content: str
    file_path: Path


class Parser:

    converter: DocumentConverter = DocumentConverter()

    def parse(self, file_path: Path) -> Document:
        result = self.converter.convert(file_path)
        docling_doc = result.document
        md = docling_doc.export_to_markdown()
        return Document(markdown_content=md, file_path=file_path)
