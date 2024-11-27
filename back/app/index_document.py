from docling.document_converter import DocumentConverter  # type: ignore[reportMissingTypeStubs]


def index_document(document_full_path: str) -> None:

    converter = DocumentConverter()
    converter.convert(document_full_path)
