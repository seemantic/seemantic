import hashlib
import os
import shutil
from functools import lru_cache
from typing import BinaryIO

from fastapi import Depends

from app.db_service import DbService
from app.settings import Settings, get_settings


class BizService:

    db_service: DbService
    seemantic_drive_root: str

    def __init__(self, db_service: DbService, seemantic_drive_root: str) -> None:
        self.db_service = db_service
        self.seemantic_drive_root = seemantic_drive_root

    def _get_full_path(self, relative_path: str) -> str:
        return f"{self.seemantic_drive_root}/{relative_path}"

    def _compute_file_hash(self, file: BinaryIO) -> str:
        return hashlib.sha256(file.read()).hexdigest()

    def create_or_update_document(self, relative_path: str, file: BinaryIO):

        full_path = self._get_full_path(relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

    def delete_document(self, relative_path: str) -> None:
        try:
            os.remove(self._get_full_path(relative_path))
        except FileNotFoundError:
            pass  # delete is idempotent


@lru_cache
def get_biz_service(settings: Settings = Depends(get_settings)) -> BizService:
    return BizService(db_service=DbService(), seemantic_drive_root=settings.seemantic_drive_root)
