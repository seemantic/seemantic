import re

from pydantic import BaseModel


class Chunk(BaseModel):
    content: str
    start_index_in_doc: int
    end_index_in_doc: int


class Chunker:

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
        for i, match in enumerate(matches):
            start_index = match.start()
            end_index = matches[i + 1].start() if i + 1 < len(matches) else len(md_content)

            chunk_content = md_content[start_index:end_index]
            chunks.append(Chunk(content=chunk_content, start_index_in_doc=start_index, end_index_in_doc=end_index))

        if len(chunks) > 0 and chunks[0].start_index_in_doc != 0:
            chunks.insert(
                0,
                Chunk(
                    content=md_content[: chunks[0].start_index_in_doc],
                    start_index_in_doc=0,
                    end_index_in_doc=chunks[0].start_index_in_doc,
                ),
            )
        return chunks
