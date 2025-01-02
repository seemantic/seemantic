import math
import re
from typing import Final

from pydantic import BaseModel


class Chunk(BaseModel):
    content: str
    start_index_in_doc: int
    end_index_in_doc: int


class Chunker:

    max_size: Final[int] = 64

    def _chunk_with_size(self, md_content: str, start_index: int, end_index: int) -> list[Chunk]:

        size = end_index - start_index
        nb_chunks = math.ceil(size / self.max_size)
        chunks: list[Chunk] = []
        for i_chunk in range(nb_chunks):
            chunk_start_index = start_index + i_chunk * self.max_size
            chunk_end_index = min(end_index, start_index + (i_chunk + 1) * self.max_size)
            chunk_content = md_content[chunk_start_index:chunk_end_index]
            chunk = Chunk(
                content=chunk_content,
                start_index_in_doc=chunk_start_index,
                end_index_in_doc=chunk_end_index,
            )
            chunks.append(chunk)
        return chunks

    def chunk(self, md_content: str) -> list[Chunk]:
        """
        Split md_content into a list of Chunk objects, where each chunk starts
        with its section header (#, ##, ###...).
        Nb: first chunk might not start with a header

        Args:
            md_content (str): The Markdown content to be chunked.

        Returns:
            list[Chunk]: A list of Chunk objects, each representing a section of the Markdown content.
        """
        chunks: list[Chunk] = []
        # Regular expression to match headers
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)

        # Find all headers and their positions
        matches = list(header_pattern.finditer(md_content))

        before_first_header = md_content[: matches[0].start()] if len(matches) > 0 else md_content
        chunks = self._chunk_with_size(before_first_header, 0, len(before_first_header))

        for i_match, match in enumerate(matches):
            start_index = match.start()
            end_index = matches[i_match + 1].start() if i_match + 1 < len(matches) else len(md_content)

            match_chunks = self._chunk_with_size(md_content, start_index, end_index)
            for chunk in match_chunks:
                chunks.append(chunk)

        return chunks
