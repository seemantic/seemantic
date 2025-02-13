from common.document import ParsedDocument
from indexer.chunker import Chunker


def test_chunk() -> None:

    md = """

    content before

# level 1 title

#notTitle

## level 2  title

### level 3 title

content
content line 2

"""
    parsed = ParsedDocument(hash="hash", markdown_content=md)
    chunks = Chunker().chunk(parsed)
    assert len(chunks) == 4
    # we can rebuild the original document from the chunks
    rebuitlt = "".join([parsed[chunk] for chunk in chunks])
    assert rebuitlt == md
    assert parsed[chunks[0]] == "\n\n    content before\n\n"


def test_chunk_with_section_too_long_before() -> None:
    content = ("1234567890azertyuoip" * 50)[: (64 * 3 + 1)]
    parsed = ParsedDocument(hash="hash", markdown_content=content)
    chunks = Chunker().chunk(parsed)
    assert len(chunks) == 4
    rebuilt = "".join([parsed[chunk] for chunk in chunks])
    assert rebuilt == content


def test_chunk_with_section_too_long() -> None:
    content = "## title \n\n ## title2 \n\n" + ("1234567890azertyuoip" * 50)[: (64 * 3 + 1)]
    parsed = ParsedDocument(hash="hash", markdown_content=content)
    chunks = Chunker().chunk(parsed)
    assert len(chunks) == 4
    rebuilt = "".join([parsed[chunk] for chunk in chunks])
    assert rebuilt == content
