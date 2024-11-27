from uuid import UUID

from fastapi import APIRouter, Form, Response, UploadFile, status
from pydantic import BaseModel

from app.biz_service import DepBizService

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


@router.put("/files/", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    response: Response,
    biz_service: DepBizService,
    relative_path: str = Form(...),
) -> None:
    biz_service.create_or_update_document(relative_path=relative_path, file=file.file)
    location = f"/files/{relative_path}"
    response.headers["Location"] = location


@router.delete("/files/{relative_path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(relative_path: str, biz_service: DepBizService) -> None:
    biz_service.delete_document(relative_path)


@router.get("/file_snippets")
async def get_file_snippets(_biz_service: DepBizService) -> ApiFileSnippetList:
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
async def create_query(
    _query: QueryRequest,
    _biz_service: DepBizService,
) -> QueryResponse:
    return QueryResponse(answer="", references=[])
