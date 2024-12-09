import hashlib
import shutil
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Annotated, BinaryIO

from fastapi import Depends

from app.model import DocumentSnippet
from app.settings import DepSettings


class BizService:

    seemantic_drive_root: Path

    def __init__(self, seemantic_drive_root: str) -> None:
        self.seemantic_drive_root = Path(seemantic_drive_root)

    def get_full_path(self, relative_path: str) -> Path:
        return self.seemantic_drive_root / relative_path

    def _compute_file_hash(self, file: BinaryIO) -> str:
        return hashlib.sha256(file.read()).hexdigest()

    def create_or_update_document(self, relative_path: str, file: BinaryIO) -> None:

        full_path = self.get_full_path(relative_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with Path(full_path).open("wb") as buffer:
            shutil.copyfileobj(file, buffer)

    def get_full_file_path_if_exists(self, relative_path: str) -> Path | None:
        full_path = self.get_full_path(relative_path)
        return full_path if full_path.is_file() else None

    def delete_document(self, relative_path: str) -> None:
        self.get_full_path(relative_path).unlink(missing_ok=True)

    def get_document_snippets(self) -> list[DocumentSnippet]:
        file_paths = [
            str(path.relative_to(self.seemantic_drive_root))
            for path in self.seemantic_drive_root.rglob("*")
            if path.is_file()
        ]
        # TODO (nicolas): add proper uuid based on DB
        return [
            DocumentSnippet(relative_path=relative_path, permanent_doc_id=uuid.uuid4(), parsed_doc_id=uuid.uuid4())
            for relative_path in file_paths
        ]


@lru_cache
def get_biz_service(settings: DepSettings) -> BizService:
    return BizService(seemantic_drive_root=settings.seemantic_drive_root)


DepBizService = Annotated[BizService, Depends(get_biz_service)]
