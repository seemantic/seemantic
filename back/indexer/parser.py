from io import BytesIO

from docling.document_converter import DocumentConverter, DocumentStream  # type: ignore[StubNotFound]

from common.document import ParsableFileType, ParsedDocument, compute_hash


class Parser:

    _converter: DocumentConverter = DocumentConverter()

    def parse(self, filetype: ParsableFileType, file_content: BytesIO) -> ParsedDocument:
        file_content.seek(0)
        if filetype == "md":
            content = file_content.read().decode("utf-8")
            content_hash = compute_hash(content)
            return ParsedDocument(hash=content_hash, markdown_content=content)
        if filetype in ("docx", "pdf"):
            document_stream = DocumentStream(name=f"dummy_stream_name.{filetype}", stream=file_content)
            result = self._converter.convert(document_stream)
            docling_doc = result.document
            md = docling_doc.export_to_markdown()
            return ParsedDocument(hash=compute_hash(md), markdown_content=md)
        error = f"Unsupported file_type {filetype}"
        raise ValueError(error)
