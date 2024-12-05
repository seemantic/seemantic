from pathlib import Path

from app.parser import Document, Parser

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


def parse(file_path: str) -> Document:
    parser = Parser()
    return parser.parse(Path(f"./tests/parsing_dataset/{file_path}"))


def test_parser_research_pdf() -> None:
    doc = parse("pdf/attention_is_all_you_need.pdf")
    check_content(doc, "## Attention Is All You Need")


def test_parser_docx() -> None:
    doc = parse("docx/file-sample_100kB.docx")
    check_content(doc, "# Lorem ipsum")


def test_parser_md() -> None:
    doc = parse("md/attention_is_all_you_need.md")
    check_content(doc, "## Attention Is All You Need")
