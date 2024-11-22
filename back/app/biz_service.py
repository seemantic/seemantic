from functools import lru_cache
import shutil
from typing import BinaryIO
from fastapi import Depends
from app.model import DocumentSnippet
from app.db_service import DbService
import os
import uuid
from app.settings import Settings, get_settings
import hashlib

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
    
    def _write_file(self, relative_path: str, file: BinaryIO):
        full_path = self._get_full_path(relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

    async def create_document(self, relative_path: str, file: BinaryIO) -> DocumentSnippet:
        self._write_file(relative_path, file)
        snippet = DocumentSnippet(
            id=uuid.uuid4(),
            relative_path=relative_path,
            content_sha256=self._compute_file_hash(file),
        )
        snippet = await self.db_service.create_document_snippet(snippet)
        return snippet

    async def update_document(self, id: uuid.UUID, relative_path: str, file: BinaryIO) -> DocumentSnippet:
        self._write_file(relative_path, file)
        update_document_snippet = await self.db_service.update_document_snippet(
            DocumentSnippet(id=id, relative_path=relative_path, content_sha256=self._compute_file_hash(file)))
        return update_document_snippet



    def delete_document(self, id: uuid.UUID) -> None:
        
        file_path = "TODO"
        try:
            os.remove(self._get_full_path(file_path))
        except FileNotFoundError:
            pass # delete is idempotent


@lru_cache
def get_biz_service(settings: Settings = Depends(get_settings)) -> BizService:
    return BizService(db_service=DbService(), seemantic_drive_root=settings.seemantic_drive_root)

