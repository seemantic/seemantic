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

    def get_full_path(self, relative_path: str) -> Path:
        return Path(f"{self.seemantic_drive_root}/{relative_path}")

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


@lru_cache
def get_biz_service(settings: DepSettings) -> BizService:
    return BizService(seemantic_drive_root=settings.seemantic_drive_root)


DepBizService = Annotated[BizService, Depends(get_biz_service)]
