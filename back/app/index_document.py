from docling.document_converter import DocumentConverter  # type: ignore


def index_document(document_full_path: str):

    converter = DocumentConverter()
    converter.convert(document_full_path)
