from fastapi import APIRouter, Response
from fastapi import UploadFile
from pydantic import BaseModel
import uuid
from uuid import UUID
from app.settings import RouteSettings
from datetime import datetime
import shutil
import os
router: APIRouter = APIRouter(prefix="/api/v1")


@router.get("/")
async def root() -> str:
    return "seemantic API says hello!"


class FileSnippet(BaseModel):
    relative_filepath: str
    uuid: UUID

class FileSnippetList(BaseModel):
    files: list[FileSnippet]

class CreateFileResponse(BaseModel):
    file_snippet: FileSnippet


def _get_file_path(settings: RouteSettings, filepath: str, filename: str) -> str:
    return f"{settings.seemantic_drive_root}/{path}/{filename}"

def _create_or_update_file(destination_relative_filepath: str, filename: str, file: UploadFile, settings: RouteSettings) -> FileSnippet:
    file_path = _get_file_path(settings, destination_path, filename=filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    snippet = FileSnippet(
        path=destination_path,
        filename=filename,
        uuid=uuid.uuid4(),
    )
    return snippet


@router.post("/files/{destination_relative_filepath}")
async def create_file(destination_relative_filepath: str, file: UploadFile, settings: RouteSettings) -> CreateFileResponse:
 
    snippet = _create_or_update_file(destination_path, filename, file, settings)
    return CreateFileResponse(file_snippet=snippet)

@router.put("/files/{document_uuid}")
async def update_file(destination_path: str, filename: str, file: UploadFile, settings: RouteSettings) -> CreateFileResponse:
    snippet = _create_or_update_file(destination_path, filename, file, settings)
    return CreateFileResponse(file_snippet=snippet)


@router.delete("/files/{destination_path}/{filename}")
async def delete_file(destination_path: str, filename: str, settings: RouteSettings) -> Response:
    file_path = _get_file_path(settings, destination_path, filename=filename)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass # delete is idempotent
    return Response(status_code=204)



@router.get("/file_snippets")
async def get_file_snippets(settings: RouteSettings)-> FileSnippetList:
    return FileSnippetList(files=[])

class Reference(BaseModel):
    file_snippet: FileSnippet
    content: str

class QueryResponse(BaseModel):
    answer: str
    references: list[Reference]

class QueryRequest(BaseModel):
    question: str

@router.post("/queries")
async def create_query(query: QueryRequest, settings: RouteSettings) -> QueryResponse:
    return QueryResponse(answer="", references=[])
