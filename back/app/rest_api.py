import logging
from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.app_services import DepDbService, DepMinioService
from app.search_engine import SearchResult
from common.db_service import DocumentView
from common.document import IndexingStatus

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
        return StreamingResponse(file, media_type="application/octet-stream")

    raise HTTPException(status_code=404, detail=f"File {relative_path} not found")


class ApiDocumentSnippet(BaseModel):
    id: UUID
    source_uri: str  # relative path within source
    raw_content_hash: str | None
    indexing_status: IndexingStatus
    parsed_content_hash: str | None


class ApiExplorer(BaseModel):
    documents: list[ApiDocumentSnippet]


def _to_api_doc(db_doc: DocumentView) -> ApiDocumentSnippet:

    return ApiDocumentSnippet(
        id=db_doc.source_document_id,
        source_uri=db_doc.source_document_uri,
        indexing_status=db_doc.indexing_status,
        raw_content_hash=db_doc.current_version.raw_document_hash if db_doc.current_version else None,
        parsed_content_hash=db_doc.indexed_version.parsed_content_hash if db_doc.indexed_version else None,
    )


@router.get("/explorer")
async def get_explorer(db_service: DepDbService) -> ApiExplorer:
    db_docs = await db_service.get_all_source_documents()

    api_docs = [_to_api_doc(doc) for doc in db_docs]
    return ApiExplorer(documents=api_docs)


class QueryResponse(BaseModel):
    answer: str
    search_result: list[SearchResult]


class QueryRequest(BaseModel):
    query: str


@router.post("/queries")
async def create_query(_query: QueryRequest) -> QueryResponse:
    return QueryResponse(answer="", search_result=[])
