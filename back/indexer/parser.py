from io import BytesIO

from docling.document_converter import DocumentConverter, DocumentStream  # type: ignore[StubNotFound]
from pydantic import BaseModel


class Document(BaseModel):
    markdown_content: str


class Parser:

    converter: DocumentConverter = DocumentConverter()

    def parse(self, file_content: BytesIO) -> Document:

        document_stream = DocumentStream(name="test", stream=file_content)
        result = self.converter.convert(document_stream)
        docling_doc = result.document
        md = docling_doc.export_to_markdown()
        return Document(markdown_content=md)
