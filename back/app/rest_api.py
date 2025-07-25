import asyncio
import logging
import urllib
import urllib.parse
from collections.abc import AsyncGenerator
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.app_services import DepDbService, DepGenerator, DepMinioService, DepSearchEngine
from app.generator import ChatMessage
from app.rest_api_data import (
    ApiChatMessage,
    ApiDocumentDelete,
    ApiDocumentSnippet,
    ApiEventType,
    ApiExplorer,
    ApiIndexedContentHash,
    ApiParsedDocument,
    ApiPresignedUrlRequest,
    ApiPresignedUrlResponse,
    ApiQuery,
    ApiQueryResponseUpdate,
    ApiSearchResult,
    ApiSearchResultChunk,
)
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


# Use minio_service to handle upload using presigned URLs
@router.post("/documents/presigned_url", status_code=status.HTTP_201_CREATED)
async def get_presigned_url(
    payload: ApiPresignedUrlRequest,
    minio_service: DepMinioService,
) -> ApiPresignedUrlResponse:
    key = get_file_path(payload.relative_path)
    url= minio_service.get_presigned_url_for_upload(key)
    return ApiPresignedUrlResponse(url=url)


@router.delete("/documents/{relative_path:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(relative_path: str, minio_service: DepMinioService) -> None:
    minio_service.delete_document(get_file_path(relative_path))



def _to_api_doc(db_doc: DbDocument) -> ApiDocumentSnippet:
    return ApiDocumentSnippet(
        uri=db_doc.uri,
        status=db_doc.status.status.value,
        error_status_message=db_doc.status.error_status_message,
        last_indexing=db_doc.last_indexing,
        indexed_content_hash=(
            ApiIndexedContentHash(
                parsed_hash=db_doc.indexed_content.parsed_hash, raw_hash=db_doc.indexed_content.raw_hash,
            )
            if db_doc.indexed_content
            else None
        ),
    )


@router.get("/documents/{encoded_uri:path}")
async def get_document(
    encoded_uri: str,
    search_engine: DepSearchEngine,
    doc_format: Annotated[Literal["parsed", "raw"], Query(alias="format")],
) -> ApiParsedDocument:
    # decode uri encoded with encodeURIComponent
    decoded_uri = urllib.parse.unquote(encoded_uri)
    if doc_format == "parsed":
        parsed_doc = await search_engine.get_document(decoded_uri)
        if parsed_doc:
            return ApiParsedDocument(hash=parsed_doc.hash, markdown_content=parsed_doc.markdown_content)
        raise HTTPException(status_code=404, detail=f"Document {decoded_uri} not found")
    if doc_format == "raw":
        # ...implement logic to return the original format if needed...
        raise HTTPException(status_code=501, detail="raw format not implemented")
    # ... handle other formats or default behavior ...
    raise HTTPException(status_code=400, detail="Unsupported or missing format")


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


@router.post("/queries")
async def create_query(
    search_engine: DepSearchEngine,
    generator: DepGenerator,
    query: ApiQuery,
) -> StreamingResponse:

    async def event_generator() -> AsyncGenerator[str, None]:
        exchanged_messages: list[ChatMessage] = []
        if not query.previous_messages:
            search_results = await search_engine.search(query.query.content)
            api_search_results = [_to_api_search_result(r) for r in search_results]
            yield _to_untyped_sse_event(
                ApiQueryResponseUpdate(
                    delta_answer=None,
                    search_results=api_search_results,
                    chat_messages_exchanged=None,
                ),
            )
            user_chat_message = generator.get_user_message(query.query.content, search_results)
            exchanged_messages.append(user_chat_message)
            answer_stream = generator.generate([user_chat_message])
        else:
            messages: list[ChatMessage] = []
            for pair in query.previous_messages:
                api_messages = pair.response.chat_messages_exchanged
                messages.extend([ChatMessage(role=message.role, content=message.content) for message in api_messages])
            user_chat_message = ChatMessage(
                role="user",
                content=query.query.content,
            )
            exchanged_messages.append(user_chat_message)
            messages.append(user_chat_message)
            answer_stream = generator.generate(messages)
        current_answer = ""
        async for chunk in answer_stream:
            current_answer += chunk
            yield _to_untyped_sse_event(
                ApiQueryResponseUpdate(
                    delta_answer=chunk,
                    search_results=None,
                    chat_messages_exchanged=None,
                ),
            )
        exchanged_messages.append(
            ChatMessage(
                role="assistant",
                content=current_answer,
            ),
        )
        yield _to_untyped_sse_event(
            ApiQueryResponseUpdate(
                delta_answer=None,
                search_results=None,
                chat_messages_exchanged=[
                    ApiChatMessage(role=m["role"], content=m["content"]) for m in exchanged_messages
                ],
            ),
        )

    return _to_streaming_response(event_generator())


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
