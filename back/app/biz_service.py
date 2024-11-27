import hashlib
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Annotated, BinaryIO

from fastapi import Depends

from app.settings import DepSettings


class BizService:

    seemantic_drive_root: str

    def __init__(self, seemantic_drive_root: str) -> None:
        self.seemantic_drive_root = seemantic_drive_root

    def _get_full_path(self, relative_path: str) -> str:
        return f"{self.seemantic_drive_root}/{relative_path}"

    def _compute_file_hash(self, file: BinaryIO) -> str:
        return hashlib.sha256(file.read()).hexdigest()

    def create_or_update_document(self, relative_path: str, file: BinaryIO) -> None:

        full_path = self._get_full_path(relative_path)
        Path(full_path).parent.mkdir(parents=True, exist_ok=True)
        with Path(full_path).open("wb") as buffer:
            shutil.copyfileobj(file, buffer)

    def delete_document(self, relative_path: str) -> None:
        try:
            Path(self._get_full_path(relative_path)).unlink(missing_ok=True)
        except FileNotFoundError:
            pass  # delete is idempotent


@lru_cache
def get_biz_service(settings: DepSettings) -> BizService:
    return BizService(seemantic_drive_root=settings.seemantic_drive_root)


DepBizService = Annotated[BizService, Depends(get_biz_service)]
