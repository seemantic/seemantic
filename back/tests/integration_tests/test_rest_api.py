# pyright: strict, reportMissingTypeStubs=false
import asyncio
import contextlib
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Literal, cast

import pytest
from httpx import ASGITransport, AsyncClient
from testcontainers.minio import MinioContainer
from testcontainers.postgres import PostgresContainer

from app.rest_api_data import (
    ApiDocumentDelete,
    ApiDocumentSnippet,
    ApiEventType,
    ApiExplorer,
    ApiQuery,
    ApiQueryMessage,
    ApiQueryResponseUpdate,
    ApiSearchResult,
)
from app.settings import Settings as AppSettings
from app.settings import get_settings as get_app_settings
from common.db_service import DbSettings
from common.minio_service import MinioSettings
from indexer.indexer import Indexer
from indexer.settings import Settings as IndexerSettings
from main import app


# cf. https://anyio.readthedocs.io/en/stable/testing.html#using-async-fixtures-with-higher-scopes
@pytest.fixture(scope="session")
def anyio_backend() -> Literal["asyncio"]:
    return "asyncio"


@pytest.fixture(scope="session")
async def test_client(anyio_backend: Literal["asyncio"]) -> AsyncGenerator[AsyncClient, None]:
    postgres = PostgresContainer("postgres:17", driver="asyncpg")
    minio: MinioContainer = MinioContainer()
    sql_init_folder = str(Path(__file__).resolve().parent.parent.parent / "postgres_db/sql_init/")
    postgres.with_volume_mapping(
        sql_init_folder,
        "/docker-entrypoint-initdb.d/",
    )
    postgres.start()
    minio.start()

    # get minio endpoint
    host_ip = minio.get_container_host_ip()
    exposed_port = minio.get_exposed_port(minio.port)
    minio_endpoint = f"{host_ip}:{exposed_port}"

    db_settings = DbSettings(
        username=postgres.username,
        password=postgres.password,
        host="localhost",
        port=postgres.get_exposed_port(postgres.port),
        database=postgres.dbname,
    )

    minio_settings = MinioSettings(
        endpoint=minio_endpoint,
        access_key=minio.access_key,
        secret_key=minio.secret_key,
        use_tls=False,
        bucket="seemantic-test",
    )

    def get_test_app_settings() -> AppSettings:
        base_settings = AppSettings()  # type: ignore[reportCallIssue]
        settings_dict = base_settings.model_dump()
        settings_dict["db"] = db_settings
        settings_dict["minio"] = minio_settings
        settings_dict["lance_db"]["minio"] = minio_settings
        return AppSettings(**settings_dict)

    def get_test_indexer_settings() -> IndexerSettings:
        base_settings = IndexerSettings()  # type: ignore[reportCallIssue]
        settings_dict = base_settings.model_dump()
        settings_dict["db"] = db_settings
        settings_dict["minio"] = minio_settings
        settings_dict["lance_db"]["minio"] = minio_settings

        return IndexerSettings(**settings_dict)

    app.dependency_overrides[get_app_settings] = get_test_app_settings

    indexer = Indexer(get_test_indexer_settings())
    indexed_task = asyncio.create_task(indexer.start())
    # wait for the indexer to be ready
    await asyncio.sleep(1)
    try:
        # see; https://fastapi.tiangolo.com/advanced/async-tests/#in-detail
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    finally:
        await stop_indexer(indexed_task)
        postgres.stop()
        minio.stop()


async def stop_indexer(indexed_task: asyncio.Task[None]) -> None:
    # Send cancellation signal
    indexed_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        # Wait for the task to actually complete its cleanup and finish
        await indexed_task


async def upload_file(test_client: AsyncClient, uri: str, file_content: bytes) -> None:
    files = {"file": ("testfile.md", file_content, "text/markdown")}
    response = await test_client.put(f"/api/v1/files/{uri}", files=files)
    assert response.status_code == 201
    assert response.headers["Location"] == f"/files/{uri}"


async def get_explorer(client: AsyncClient) -> list[ApiDocumentSnippet]:
    result = await client.get("/api/v1/explorer")
    json = result.json()
    explorer = ApiExplorer.model_validate(json)
    return explorer.documents


DocEvent = tuple[ApiEventType | Literal["keep_alive"], ApiDocumentSnippet | ApiDocumentDelete | None]


def parse_event(event: str) -> DocEvent:
    # Split into lines and extract event type and data
    lines = event.split("\n")
    event_type = cast("ApiEventType", lines[0].split(": ")[1])
    data = lines[1].split(": ")[1]

    if event_type == "delete":
        return event_type, ApiDocumentDelete.model_validate_json(data)
    return event_type, ApiDocumentSnippet.model_validate_json(data)


async def listen_docs(client: AsyncClient, nb_events: int) -> list[DocEvent]:
    response = await client.get("/api/v1/document_events", params={"nb_events": nb_events})
    assert response.status_code == 200
    events: list[DocEvent] = []
    for sse_line in response.text.split("\n\n"):
        if sse_line.startswith("event: "):
            event_type, event_data = parse_event(sse_line)
            events.append((event_type, event_data))
        elif sse_line.startswith(":ka"):
            events.append(("keep_alive", None))

    return events


def listen_docs_task(
    test_client: AsyncClient,
    nb_events: int,
) -> asyncio.Task[list[DocEvent]]:
    return asyncio.create_task(listen_docs(test_client, nb_events))


def check_events_valid(uri: str, events: list[DocEvent]) -> None:
    assert len(events) == 3

    insert, val_pending = events[0]
    update, val_indexing = events[1]
    update_success, val_success = events[2]

    assert insert == "update"
    assert update == "update"
    assert update_success == "update"

    assert isinstance(val_pending, ApiDocumentSnippet)
    assert val_pending.status == "pending"
    assert isinstance(val_indexing, ApiDocumentSnippet)
    assert val_indexing.status == "indexing"
    assert isinstance(val_success, ApiDocumentSnippet)
    assert val_success.status == "indexing_success"
    assert val_pending.uri == uri
    assert val_indexing.uri == uri
    assert val_success.uri == uri


async def query(client: AsyncClient, query: str) -> ApiQueryResponseUpdate:
    query_message = ApiQueryMessage(content=query)
    query_json = ApiQuery(query=query_message, previous_messages=[]).model_dump()
    response = await client.post("/api/v1/queries", json=query_json)
    assert response.status_code == 200

    full_response_content: str = ""
    search_results: list[ApiSearchResult] = []
    # split will add en empty element after the last message, we remove it
    for sse_line in response.text.split("\n\n")[:-1]:
        json = sse_line.removeprefix("data: ")
        update = ApiQueryResponseUpdate.model_validate_json(json)
        full_response_content += update.delta_answer or ""
        if update.search_result:
            search_results = update.search_result
    return ApiQueryResponseUpdate(
        delta_answer=full_response_content,
        search_result=search_results,
        chat_messages_exchanged=None,
    )



@pytest.mark.anyio
async def test_upload_file(test_client: AsyncClient) -> None:
    # 1. update a file, check we get the updates
    uri = "test/path/to/file.md"
    task = listen_docs_task(test_client, 3)
    await upload_file(test_client, uri, b"# What is seemantic ? It's a RAG")
    result = await task
    check_events_valid(uri, result)


    # 2. update the same file, check we don't get any update
    task = listen_docs_task(test_client, 1)
    await upload_file(test_client, uri, b"# What is seemantic ? It's a RAG")
    result = await task
    assert result[0][0] == "keep_alive"

    # 3. make a request
    response = await query(test_client, "what is seemantic?")
    assert response.delta_answer
    assert "rag" in response.delta_answer.lower()
    explorer = await get_explorer(test_client)
    assert len(explorer) == 1
    doc = explorer[0]
    assert doc.uri == uri
    assert doc.status == "indexing_success"

    # 4. updata and make a request
    await upload_file(test_client, uri, b"# What is seemantic ? It's a webapp")
    await asyncio.sleep(2)
    response = await query(test_client, "what is seemantic?")
    assert response.delta_answer
    assert "web" in response.delta_answer.lower()
    assert "rag" not in response.delta_answer.lower()

    # 5. delete doc
    await test_client.delete(f"/api/v1/files/{uri}")
    await asyncio.sleep(1)
    explorer = await get_explorer(test_client)
    assert len(explorer) == 0
