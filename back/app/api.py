from fastapi import APIRouter
from fastapi import UploadFile
from pydantic import BaseModel
from uuid import UUID

router: APIRouter = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "seemantic API says hello!"}


class FileSnippet(BaseModel):
    filename: str
    uuid: UUID

class FileSnippetListResponse(BaseModel):
    files: list[FileSnippet]


@router.put("/file")
async def create_or_update_file(file: UploadFile):
    pass

@router.get("/file_snippets")
async def get_file_snippets()-> FileSnippetListResponse:
    return FileSnippetListResponse(files=[])


@router.delete("/files/{file_uuid}")
async def delete_file(file_uuid: UUID):
    pass

class Reference(BaseModel):
    file_snippet: FileSnippet
    content: str

class AnswerResponse(BaseModel):
    answer: str
    references: list[Reference]

@router.get("answer")
async def get_answer() -> AnswerResponse:
    return AnswerResponse(answer="", references=[])