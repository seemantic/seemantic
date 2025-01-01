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

        # Iterate through headers to create chunks
        for i_match, match in enumerate(matches):
            start_index = match.start()
            end_index = matches[i_match + 1].start() if i_match + 1 < len(matches) else len(md_content)

            size = end_index - start_index
            nb_chunks = math.ceil(size / self.max_size)
            for i_chunk in range(nb_chunks):
                chunk_start_index = start_index + i_chunk * self.max_size
                chunk_end_index = start_index + (i_chunk + 1) * self.max_size
                chunk_end_index = min(chunk_end_index, end_index)
                chunk_content = md_content[chunk_start_index:chunk_end_index]
                chunk = Chunk(
                    content=chunk_content,
                    start_index_in_doc=chunk_start_index,
                    end_index_in_doc=chunk_end_index,
                )
                chunks.append(chunk)
        # Add the first chunk if it doesn't start with a header
        # here manage split also Nico
        if len(chunks) > 0 and chunks[0].start_index_in_doc != 0:
            first_chunk_content = Chunk(
                content=md_content[: chunks[0].start_index_in_doc],
                start_index_in_doc=0,
                end_index_in_doc=chunks[0].start_index_in_doc,
            )
            chunks.insert(0, first_chunk_content)
        return chunks
