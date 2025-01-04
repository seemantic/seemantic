from io import BytesIO
from pathlib import Path

from common.document import ParsableFileType
from indexer.parser import Document, Parser

# working document formats:
# -pdf
# -docx
# -markdown

# tested butnot working
# -txt
# -doc

# doc/docx file examples from https://file-examples.com/index.php/sample-documents-download/sample-doc-download/


def check_content(doc: Document, expected_content: str) -> None:
    assert expected_content in doc.markdown_content


def parse(filetype: ParsableFileType, file_path: str) -> Document:
    parser = Parser()
    path = Path(f"./tests/parsing_dataset/{file_path}")
    doc_bytes = path.read_bytes()
    bytesio = BytesIO(doc_bytes)
    return parser.parse(filetype, bytesio)


def test_parser_research_pdf() -> None:
    doc = parse("pdf", "pdf/attention_is_all_you_need.pdf")
    check_content(doc, "## Attention Is All You Need")


def test_parser_docx() -> None:
    doc = parse("docx", "docx/file-sample_100kB.docx")
    check_content(doc, "# Lorem ipsum")


def test_parser_md() -> None:
    doc = parse("md", "md/attention_is_all_you_need.md")
    check_content(doc, "## Attention Is All You Need")
