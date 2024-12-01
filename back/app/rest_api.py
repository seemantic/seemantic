from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
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


# relative_path:path is a fastApi "path converter" to capture a path parameter with "/" inside 'relative_path'
@router.put("/files/{relative_path:path}", status_code=status.HTTP_201_CREATED)
async def upsert_file(
    relative_path: str,
    file: UploadFile,
    response: Response,
    biz_service: DepBizService,
) -> None:
    biz_service.create_or_update_document(relative_path=relative_path, file=file.file)
    location = f"/files/{relative_path}"
    response.headers["Location"] = location


@router.delete("/files/{relative_path:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(relative_path: str, biz_service: DepBizService) -> None:
    biz_service.delete_document(relative_path)


@router.get("/files/{relative_path:path}")
async def get_file(relative_path: str, biz_service: DepBizService) -> FileResponse:
    doc_full_path = biz_service.get_full_file_path_if_exists(relative_path)
    if doc_full_path:
        return FileResponse(doc_full_path)

    raise HTTPException(status_code=404, detail=f"File {relative_path} not found")


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
