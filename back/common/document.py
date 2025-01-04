from typing import Literal, get_args

ParsableFileType = Literal["pdf", "docx", "md"]


def is_parsable(filetype: str | None) -> bool:
    return filetype is not None and filetype in get_args(ParsableFileType)
