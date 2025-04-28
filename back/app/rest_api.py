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
from app.generator import ChatMessage
from app.search_engine import SearchResult
from app.settings import DepSettings
from common.db_service import DbDocument, DbEventType, DbIndexedDocumentEvent

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
    uri: str  # relative path within source
    status: Literal["pending", "indexing", "indexing_success", "indexing_error"]
    error_status_message: str | None
    last_indexing: datetime | None


class ApiDocumentDelete(BaseModel):
    uri: str


class ApiExplorer(BaseModel):
    documents: list[ApiDocumentSnippet]


class ApiSearchResultChunk(BaseModel):
    content: str
    start_index_in_doc: int
    end_index_in_doc: int


class ApiSearchResult(BaseModel):
    document_uri: str
    chunks: list[ApiSearchResultChunk]



class ApiQueryResponseUpdate(BaseModel):
    # if not None, it's the continuation of the answer
    # if None, keep the previous answer.
    delta_answer: str | None
    # if None, keep the previous result.
    # if not None, it replace the previous search result
    search_result: list[ApiSearchResult] | None


class ApiQueryResponseMessage(BaseModel):
    answer: str
    search_result: list[ApiSearchResult]

class ApiQueryMessage(BaseModel):
    content: str


def _to_api_doc(db_doc: DbDocument) -> ApiDocumentSnippet:
    return ApiDocumentSnippet(
        uri=db_doc.uri,
        status=db_doc.status.status.value,
        error_status_message=db_doc.status.error_status_message,
        last_indexing=db_doc.last_indexing,
    )


@router.get("/explorer")
async def get_explorer(db_service: DepDbService, settings: DepSettings) -> ApiExplorer:
    db_docs = await db_service.get_all_documents(settings.indexer_version)

    api_docs = [_to_api_doc(doc) for doc in db_docs]
    return ApiExplorer(documents=api_docs)




def _to_api_search_result(search_result: SearchResult) -> ApiSearchResult:
    return ApiSearchResult(
        document_uri=search_result.db_document.uri,
        chunks=[
            ApiSearchResultChunk(
                content=search_result.parsed_document[c.chunk],
                start_index_in_doc=c.chunk.start_index_in_doc,
                end_index_in_doc=c.chunk.end_index_in_doc,
            )
            for c in search_result.chunks
        ],
    )


class ApiQuery(BaseModel):
    last_user_message: ApiQueryMessage
    previous_messages: list[ApiQueryMessage | ApiQueryResponseMessage]


@router.post("/queries")
async def create_query(
    search_engine: DepSearchEngine, generator: DepGenerator, query: ApiQuery,
) -> StreamingResponse:

    search_results = None
    if not query.previous_messages:
        search_results = await search_engine.search(query.last_user_message.content)

    async def event_generator() -> AsyncGenerator[str, None]:
        if search_results:
            yield _to_untyped_sse_event(
                ApiQueryResponseUpdate(
                    delta_answer=None,
                    search_result=[_to_api_search_result(r) for r in search_results],
                ),
            )
            answer_stream = generator.generate(query.last_user_message.content, search_results)
        else:
            answer_stream = generator.generate_from_conversation(
                query.last_user_message.content,
                [ChatMessage(role=message.role, content=message.content) for message in query.previous_messages],
            )
        async for chunk in answer_stream:
            yield _to_untyped_sse_event(
                ApiQueryResponseUpdate(
                    delta_answer=chunk,
                    search_result=None,
                ),
            )

    return _to_streaming_response(event_generator())

    raise HTTPException(status_code=400, detail="Only one message is supported for now")


ApiEventType = Literal["update", "delete"]


def _to_api_event_type(db_event_type: DbEventType) -> ApiEventType:
    return "delete" if db_event_type == "delete" else "update"


def _to_sse_event(event_type: str, data: BaseModel) -> str:
    return f"event: {event_type}\ndata: {data.model_dump_json()}\n\n"


def _to_untyped_sse_event(data: BaseModel) -> str:
    return f"data: {data.model_dump_json()}\n\n"


@router.get("/document_events")
async def subscribe_to_indexed_documents_changes(
    db_service: DepDbService,
    request: Request,
    nb_events: int | None = None,
    keep_alive_interval: float = 20.0,
) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[str, None]:
        event_queue: asyncio.Queue[DbIndexedDocumentEvent] = asyncio.Queue()
        await db_service.listen_to_indexed_documents_changes(event_queue, 1)
        events_sent = 0
        try:
            while True:
                if await request.is_disconnected():
                    break

                if nb_events is not None and events_sent >= nb_events:
                    break

                # Wait for message with timeout to check for disconnects
                try:
                    message = await asyncio.wait_for(event_queue.get(), timeout=keep_alive_interval)
                    api_event = (
                        _to_api_doc(message.document)
                        if message.event_type != "delete"
                        else ApiDocumentDelete(uri=message.document.uri)
                    )
                    yield _to_sse_event(_to_api_event_type(message.event_type), api_event)
                    events_sent += 1
                except TimeoutError:
                    # Send keep-alive comment, message starting swith ":" are ignored by the client, this prevents the connection from timing out
                    yield ":ka\n\n"
                    events_sent += 1
        finally:
            # Clean up on disconnect
            await db_service.removed_listener_to_indexed_documents_changes(event_queue)

    return _to_streaming_response(event_generator())


def _to_streaming_response(
    generator: AsyncGenerator[str, None],
) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
