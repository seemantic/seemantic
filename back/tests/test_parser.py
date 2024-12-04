from app.parser import Parser, Document
from pathlib import Path

# document formats
# pdf
# doc
# docx
# txt
# markdown

# file examples:
# https://file-examples.com/index.php/sample-documents-download/sample-doc-download/



def check_content(doc: Document, expected_content: str) -> None:
    assert expected_content in doc.markdown_content

def parse(file_path: str) -> Document:
    parser = Parser()
    return parser.parse(Path(f"./tests/parsing_dataset/{file_path}"))

def test_parser_research_pdf() -> None:
    doc = parse("pdf/attention_is_all_you_need.pdf")
    check_content(doc, "## Attention Is All You Need")

def test_parser_doc() -> None:
    doc = parse("doc/file-sample_100kB.doc")
    check_content(doc, "## Lorem ipsum dolor sit amet")

def test_parser_docx() -> None:
    doc = parse("docx/file-sample_100kB.docx")
    check_content(doc, "# Lorem ipsum")
