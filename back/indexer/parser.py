from io import BytesIO

from docling.document_converter import DocumentConverter, DocumentStream  # type: ignore[StubNotFound]
from xxhash import xxh3_128_hexdigest

from common.document import ParsableFileType, ParsedDocument


class Parser:

    _converter: DocumentConverter = DocumentConverter()

    def parse(self, filename: str, filetype: ParsableFileType, file_content: BytesIO) -> ParsedDocument:
        file_content.seek(0)
        if filetype == "md":
            content = file_content.read().decode("utf-8")
            content_hash = xxh3_128_hexdigest(content)
            return ParsedDocument(hash=content_hash, markdown_content=content)
        if filetype in ("docx", "pdf"):
            document_stream = DocumentStream(name=filename, stream=file_content)
            result = self._converter.convert(document_stream)
            docling_doc = result.document
            content = docling_doc.export_to_markdown()
            content_hash = xxh3_128_hexdigest(content)
            return ParsedDocument(hash=content_hash, markdown_content=content)
        error = f"Unsupported file_type {filetype}"
        raise ValueError(error)
