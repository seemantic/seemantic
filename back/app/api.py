from fastapi import APIRouter
from fastapi import UploadFile
from pydantic import BaseModel
from uuid import UUID

router: APIRouter = APIRouter(prefix="/api/v1")


@router.get("/")
async def root() -> str:
    return "seemantic API says hello!"


class FileSnippet(BaseModel):
    filename: str
    uuid: UUID

class FileSnippetListResponse(BaseModel):
    files: list[FileSnippet]


@router.post("/files")
async def create_file(file: UploadFile):
    pass

@router.put("/files/{file_uuid}")
async def update_file(file_id: str, file: UploadFile):
    pass

@router.delete("/files/{file_uuid}")
async def delete_file(file_uuid: UUID):
    pass

@router.get("/file_snippets")
async def get_file_snippets()-> FileSnippetListResponse:
    return FileSnippetListResponse(files=[])


class Reference(BaseModel):
    file_snippet: FileSnippet
    content: str

class QueryResponse(BaseModel):
    answer: str
    references: list[Reference]

class QueryRequest(BaseModel):
    question: str

@router.post("/queries")
async def create_query(query: QueryRequest) -> QueryResponse:
    return QueryResponse(answer="", references=[])
