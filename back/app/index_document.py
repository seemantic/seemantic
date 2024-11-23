from docling.document_converter import DocumentConverter


def index_document(document_full_path: str):

    converter = DocumentConverter()
    result = converter.convert(document_full_path)
    print(result.document.export_to_markdown()) 


