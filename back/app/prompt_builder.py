import re

from pydantic import BaseModel

from common.document import Chunk, ParsedDocument
from common.vector_db import ChunkResult


class PromptBuilder(BaseModel):

    header_pattern: re.Pattern[str] = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)

    def merge_extend_passages(self, parsed_document: ParsedDocument, chunks: list[ChunkResult]) -> list[ChunkResult]:
        """
        extends passages to the document section, including the header
        merges passages if they are from 2 sections next to each other
        """
        content = parsed_document.markdown_content
        matches = self.header_pattern.finditer(content)
        start_sections: list[int] = [m.start() for m in matches]
        start_sections.append(len(content))  # fictive section starting after the end of the document to simplify loop
        points: list[tuple[int, float]] = [(p.chunk.start_index_in_doc, p.distance) for p in chunks]
        points.extend((p.chunk.end_index_in_doc, p.distance) for p in chunks)

        section_indexes_to_includes: dict[int, float] = {}
        current_section_index = 0
        current_point_index = 0
        while current_point_index < len(points):
            point, distance = points[current_point_index]

            if point >= start_sections[current_section_index] and point <= start_sections[current_section_index + 1]:
                section_indexes_to_includes[current_section_index] = min(
                    section_indexes_to_includes.get(current_section_index, distance),
                    distance,
                )
                current_point_index += 1
            elif point >= start_sections[current_section_index + 1]:
                current_section_index += 1
            else:
                current_point_index += 1

        result: list[ChunkResult] = [
            ChunkResult(
                chunk=Chunk(start_index_in_doc=start_sections[idx_s], end_index_in_doc=start_sections[idx_s + 1]),
                distance=distance,
            )
            for idx_s, distance in section_indexes_to_includes.items()
        ]

        return result
