import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from io import BytesIO
from threading import Thread

from fastapi import APIRouter, FastAPI, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.biz_service import DepBizService
from app.minio_service import DepMinioService, get_minio_service
from app.search_engine import SearchResult
from app.settings import get_settings

router: APIRouter = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


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
    minio_service.create_or_update_document(relative_path=relative_path, file=binary)
    location = f"/files/{relative_path}"
    response.headers["Location"] = location


@router.delete("/files/{relative_path:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(relative_path: str, minio_service: DepMinioService) -> None:
    minio_service.delete_document(relative_path)


@router.get("/files/{relative_path:path}")
async def get_file(relative_path: str, minio_service: DepMinioService) -> StreamingResponse:
    file = minio_service.get_file(relative_path)
    if file:
        return StreamingResponse(file, media_type="application/octet-stream")

    raise HTTPException(status_code=404, detail=f"File {relative_path} not found")


@router.get("/file_snippets")
async def get_file_snippets(minio_service: DepMinioService) -> ApiFileSnippetList:
    minio_service.get_files()
    paths: list[str] = minio_service.get_files()
    return ApiFileSnippetList(files=[ApiFileSnippet(relative_path=path) for path in paths])


class QueryResponse(BaseModel):
    answer: str
    search_result: list[SearchResult]


class QueryRequest(BaseModel):
    query: str


@router.post("/queries")
async def create_query(
    _query: QueryRequest,
    _biz_service: DepBizService,
) -> QueryResponse:
    return QueryResponse(answer="", search_result=[])


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:

    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    # NB: ignore false positive related to Settings not hashable because it's not frozen at the type level (but it's frozen as config level)
    minio_service = get_minio_service(settings)  # type: ignore[ReportUnknownMember]]

    thread = Thread(target=minio_service.listen_notifications, daemon=True)
    thread.start()
    logger.info("Background task started.")
    try:
        yield  # Pass control back to FastAPI
    finally:
        logger.info("Background task stopping...")
