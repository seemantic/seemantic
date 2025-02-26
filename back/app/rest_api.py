import logging
from datetime import datetime
from io import BytesIO
from typing import Literal

from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.app_services import DepDbService, DepMinioService, DepSearchEngine
from app.search_engine import SearchResult
from common.db_service import DbDocument

router: APIRouter = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)
seemantic_drive_prefix = "seemantic_drive/"


def get_file_path(relative_path: str) -> str:
    return f"{seemantic_drive_prefix}{relative_path}"


@router.get("/")
async def root() -> str:
    return "seemantic API says hello!"


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
        return StreamingResponse(file.content, media_type="application/octet-stream")

    raise HTTPException(status_code=404, detail=f"File {relative_path} not found")


class ApiDocumentSnippet(BaseModel):
    source_uri: str  # relative path within source
    status: Literal["pending", "indexing", "indexing_success", "indexing_error"]
    error_status_message: str | None
    last_indexing: datetime | None


class ApiExplorer(BaseModel):
    documents: list[ApiDocumentSnippet]


def _to_api_doc(db_doc: DbDocument) -> ApiDocumentSnippet:

    return ApiDocumentSnippet(
        source_uri=db_doc.uri,
        status=db_doc.status.status.value,
        error_status_message=db_doc.status.error_status_message,
        last_indexing=db_doc.indexed_content.last_indexing if db_doc.indexed_content else None,
    )


@router.get("/explorer")
async def get_explorer(db_service: DepDbService) -> ApiExplorer:
    db_docs = await db_service.get_all_documents()

    api_docs = [_to_api_doc(doc) for doc in db_docs]
    return ApiExplorer(documents=api_docs)


class QueryResponse(BaseModel):
    answer: str
    search_result: list[SearchResult]
    chunks_content: dict[str, float]  # to delete


class QueryRequest(BaseModel):
    query: str


@router.post("/queries")
async def create_query(search_engine: DepSearchEngine, query: QueryRequest) -> QueryResponse:
    search_results = await search_engine.search(query.query)
    chunks_content = {
        result.parsed_document[chunk.chunk]: chunk.distance for result in search_results for chunk in result.chunks
    }
    return QueryResponse(answer="", search_result=search_results, chunks_content=chunks_content)
