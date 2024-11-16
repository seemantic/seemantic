from fastapi import APIRouter
from fastapi import UploadFile
from pydantic import BaseModel
from uuid import UUID
from app.settings import RouteSettings

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
async def create_file(file: UploadFile, settings: RouteSettings):
    pass

@router.put("/files/{file_uuid}")
async def update_file(file_id: str, file: UploadFile, settings: RouteSettings):
    pass

@router.delete("/files/{file_uuid}")
async def delete_file(file_uuid: UUID, settings: RouteSettings):
    pass

@router.get("/file_snippets")
async def get_file_snippets(settings: RouteSettings)-> FileSnippetListResponse:
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
async def create_query(query: QueryRequest, settings: RouteSettings) -> QueryResponse:
    return QueryResponse(answer="", references=[])
