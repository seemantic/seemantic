from pathlib import Path

from docling.document_converter import ConversionResult, DocumentConverter  # type: ignore[StubNotFound]
from pydantic import BaseModel


class Block(BaseModel):
    content: str
    level: int  # start with 0 (document title)


class Document(BaseModel):
    blocks: list[Block]


def _docling_result_to_doc(_: ConversionResult) -> Document:
    return Document(blocks=[])


class Parser:

    def parse(self, file_path: Path) -> Document:
        converter = DocumentConverter()
        result = converter.convert(file_path)
        return _docling_result_to_doc(result)

    # token indexing ?
