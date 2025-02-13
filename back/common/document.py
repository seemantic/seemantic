from typing import Literal, get_args

from pydantic import BaseModel

ParsableFileType = Literal["pdf", "docx", "md"]


def is_parsable(filetype: str | None) -> bool:
    return filetype is not None and filetype in get_args(ParsableFileType)


class Chunk(BaseModel):
    start_index_in_doc: int
    end_index_in_doc: int


class Embedding(BaseModel):
    embedding: list[float]


class EmbeddedChunk(BaseModel):
    chunk: Chunk
    embedding: Embedding


class ParsedDocument(BaseModel):
    hash: str
    markdown_content: str

    def __getitem__(self, chunk: Chunk) -> str:
        return self.markdown_content[chunk.start_index_in_doc : chunk.end_index_in_doc]
