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

    chunks = Chunker().chunk(md)
    assert len(chunks) == 4
    # we can rebuild the original document from the chunks
    rebuitlt = "".join([chunk.content for chunk in chunks])
    assert rebuitlt == md
    # indexes are corrects
    for chunk in chunks:
        assert md[chunk.start_index_in_doc : chunk.end_index_in_doc] == chunk.content
    assert chunks[0].content == "\n\n    content before\n\n"
