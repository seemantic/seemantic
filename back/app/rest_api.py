import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from io import BytesIO
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.app_services import DepDbService, DepGenerator, DepMinioService, DepSearchEngine
from app.search_engine import SearchResult
from app.settings import DepSettings
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
        last_indexing=db_doc.last_indexing,
    )


@router.get("/explorer")
async def get_explorer(db_service: DepDbService, settings: DepSettings) -> ApiExplorer:
    db_docs = await db_service.get_all_documents(settings.indexer_version)

    api_docs = [_to_api_doc(doc) for doc in db_docs]
    return ApiExplorer(documents=api_docs)


class QueryResponse(BaseModel):
    answer: str
    search_result: list[SearchResult]
    chunks_content: dict[str, float]  # to delete


class QueryRequest(BaseModel):
    query: str


@router.post("/queries")
async def create_query(search_engine: DepSearchEngine, generator: DepGenerator, query: QueryRequest) -> QueryResponse:
    search_results = await search_engine.search(query.query)
    chunks_content = {
        result.parsed_document[chunk.chunk]: chunk.distance for result in search_results for chunk in result.chunks
    }
    answer = generator.generate(query.query, search_results)
    return QueryResponse(answer=answer, search_result=search_results, chunks_content=chunks_content)


@router.get("/sse")
async def subscribe_to_indexed_documents_changes(db_service: DepDbService, request: Request) -> StreamingResponse:

    async def event_generator() -> AsyncGenerator[str, None]:

        event_queue: asyncio.Queue[str] = asyncio.Queue()
        await db_service.listen_to_indexed_documents_changes(event_queue, 1)
        try:
            while True:
                if await request.is_disconnected():
                    break

                # Wait for message with timeout to check for disconnects
                try:
                    message = await asyncio.wait_for(event_queue.get(), timeout=20.0)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    # Send keep-alive comment, message starting swith ":" are ignored by the client, this prevents the connection from timing out
                    yield ":ka\n\n"
        finally:
            # Clean up on disconnect
            await db_service.removed_listener_to_indexed_documents_changes(event_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
