from io import BytesIO

from docling.document_converter import DocumentConverter, DocumentStream  # type: ignore[StubNotFound]
from pydantic import BaseModel

from common.document import SupportedFileType


class Document(BaseModel):
    markdown_content: str


class Parser:

    converter: DocumentConverter = DocumentConverter()

    def parse(self, file_type: SupportedFileType, file_content: BytesIO) -> Document:

        if file_type == "md":
            return Document(markdown_content=file_content.read().decode("utf-8"))
        if file_type in ("docx", "pdf"):
            document_stream = DocumentStream(name="test", stream=file_content)
            result = self.converter.convert(document_stream)
            docling_doc = result.document
            md = docling_doc.export_to_markdown()
            return Document(markdown_content=md)
        error = f"Unsupported file_type {file_type}"
        raise ValueError(error)
