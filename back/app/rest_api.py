import logging
from io import BytesIO

from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.minio_service import DepMinioService
from app.search_engine import SearchResult

router: APIRouter = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)
seemantic_drive_prefix = "seemantic_drive/"


def get_file_path(relative_path: str) -> str:
    return f"{seemantic_drive_prefix}{relative_path}"


@router.get("/")
async def root() -> str:
    return "seemantic API says hello!"


class ApiFileSnippet(BaseModel):
    relative_path: str


class ApiFileSnippetList(BaseModel):
    files: list[ApiFileSnippet]


# relative_path:path is a fastApi "path converter" to capture a path parameter with "/" inside 'relative_path'
@router.put("/files/{relative_path:path}", status_code=status.HTTP_201_CREATED)
async def upsert_file(relative_path: str, file: UploadFile, response: Response, minio_service: DepMinioService) -> None:
    binary = BytesIO(file.file.read())
    minio_service.create_or_update_document(key=get_file_path(relative_path), file=binary)
    location = f"/files/{relative_path}"
    response.headers["Location"] = location


@router.delete("/files/{relative_path:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(relative_path: str, minio_service: DepMinioService) -> None:
    minio_service.delete_document(get_file_path(relative_path))


@router.get("/files/{relative_path:path}")
async def get_file(relative_path: str, minio_service: DepMinioService) -> StreamingResponse:
    file = minio_service.get_document(get_file_path(relative_path))
    if file:
        return StreamingResponse(file, media_type="application/octet-stream")

    raise HTTPException(status_code=404, detail=f"File {relative_path} not found")


@router.get("/file_snippets")
async def get_file_snippets(minio_service: DepMinioService) -> ApiFileSnippetList:
    paths: list[str] = minio_service.get_all_documents(prefix=seemantic_drive_prefix)
    return ApiFileSnippetList(files=[ApiFileSnippet(relative_path=path) for path in paths])


class QueryResponse(BaseModel):
    answer: str
    search_result: list[SearchResult]


class QueryRequest(BaseModel):
    query: str


@router.post("/queries")
async def create_query(_query: QueryRequest) -> QueryResponse:
    return QueryResponse(answer="", search_result=[])
