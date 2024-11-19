from functools import lru_cache
import shutil
from fastapi import Depends, UploadFile
from app.model import DocumentSnippet
from app.db_service import DbService
import os
import uuid
from app.settings import Settings, get_settings

class BizService:

    db_service: DbService
    seemantic_drive_root: str

    def __init__(self, db_service: DbService, seemantic_drive_root: str) -> None:
        self.db_service = db_service
        self.seemantic_drive_root = seemantic_drive_root
    
    def _get_full_path(self, relative_path: str) -> str:
        return f"{self.seemantic_drive_root}/{relative_path}"

    def create_document(self, relative_path: str, file: UploadFile) -> DocumentSnippet:
        
        full_path = self._get_full_path(relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        snippet = DocumentSnippet(
            id=uuid.uuid4(),
            relative_path=relative_path
        )
        return snippet
    

    def delete_document(self, id: uuid.UUID) -> None:
        file_path = "TODO"
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass # delete is idempotent


@lru_cache
def get_biz_service(settings: Settings = Depends(get_settings)) -> BizService:
    return BizService(db_service=DbService(), seemantic_drive_root=settings.seemantic_drive_root)

