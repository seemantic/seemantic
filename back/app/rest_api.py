from uuid import UUID

from fastapi import APIRouter, Depends, Form, UploadFile
from pydantic import BaseModel

from app.biz_service import BizService, get_biz_service
from app.model import DocumentSnippet

router: APIRouter = APIRouter(prefix="/api/v1")


@router.get("/")
async def root() -> str:
    return "seemantic API says hello!"


class ApiFileSnippet(BaseModel):
    relative_path: str
    id: UUID
    content_sha256: str

class ApiFileSnippetList(BaseModel):
    files: list[ApiFileSnippet]


class FileResponse(BaseModel):
    file_snippet: ApiFileSnippet



@router.post("/files/")
async def upload_file(file: UploadFile, relative_path: str = Form(...), biz_service: BizService = Depends(get_biz_service)) -> FileResponse:
    snippet = await biz_service.create_document(relative_path=relative_path, file=file.file)
    return FileResponse(file_snippet=_to_api_file_snippet(snippet))

def _to_api_file_snippet(snippet: DocumentSnippet) -> ApiFileSnippet:
    return ApiFileSnippet(relative_path=snippet.relative_path, id=snippet.id, content_sha256=snippet.content_sha256)


@router.get("/file_snippets")
async def get_file_snippets(biz_service: BizService = Depends(get_biz_service))-> ApiFileSnippetList:
    return ApiFileSnippetList(files=[])

class Reference(BaseModel):
    file_snippet: ApiFileSnippet
    content: str

class QueryResponse(BaseModel):
    answer: str
    references: list[Reference]

class QueryRequest(BaseModel):
    question: str

@router.post("/queries")
async def create_query(query: QueryRequest, biz_service: BizService = Depends(get_biz_service)) -> QueryResponse:
    return QueryResponse(answer="", references=[])
