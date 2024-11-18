import shutil
from fastapi import UploadFile
from app.model import DocumentSnippet
from back.app.db import DbService
import os
import uuid

class Service:

    db: DbService
    seemantic_drive_root_url: str

    def __init__(self, db: DbService, seemantic_drive_root_url: str) -> None:
        self.db = db
        self.seemantic_drive_root_url = seemantic_drive_root_url
    
    def _get_full_path(self, relative_filepath: str) -> str:
        return f"{self.seemantic_drive_root_url}/{relative_filepath}"

    def _get_relative_filepath(self,relative_path: str, filename: str) -> str:
        return f"{relative_path}/{filename}"


    def create_document(self, relative_path: str, filename: str, file: UploadFile) -> DocumentSnippet:
        
        relative_filepath = self._get_relative_filepath( relative_path, filename)
        file_path = self._get_full_path(relative_filepath)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        snippet = DocumentSnippet(
            id=uuid.uuid4(),
            uri=relative_filepath
        )
        return snippet