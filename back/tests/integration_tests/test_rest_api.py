# pyright: strict, reportMissingTypeStubs=false
import asyncio
from pathlib import Path
from time import sleep
from httpx import ASGITransport, AsyncClient
import pytest

from testcontainers.minio import MinioContainer
from testcontainers.postgres import PostgresContainer

from app.settings import Settings as AppSettings
from app.settings import get_settings as get_app_settings
from app.rest_api import ApiDocumentDelete, ApiDocumentSnippet, ApiExplorer
from common.db_service import DbSettings
from common.minio_service import MinioSettings
from indexer.indexer import Indexer
from indexer.settings import Settings as IndexerSettings
from main import app
from typing import AsyncGenerator, Literal, Tuple


# cf. https://anyio.readthedocs.io/en/stable/testing.html#using-async-fixtures-with-higher-scopes
@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'



@pytest.fixture(scope="session")
async def test_client(anyio_backend: Literal['asyncio']) -> AsyncGenerator[AsyncClient, None]:
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
        return AppSettings(**settings_dict) 

    def get_test_indexer_settings() -> IndexerSettings:
        base_settings = IndexerSettings()  # type: ignore[reportCallIssue]
        settings_dict = base_settings.model_dump()
        settings_dict["db"] = db_settings
        settings_dict["minio"] = minio_settings
        return IndexerSettings(**settings_dict)

    app.dependency_overrides[get_app_settings] = get_test_app_settings
    
    indexer = Indexer(get_test_indexer_settings())
    indexed_task = asyncio.create_task(indexer.start())
    sleep(1)
    try:
        # see; https://fastapi.tiangolo.com/advanced/async-tests/#in-detail
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    finally:
        indexed_task.cancel()
        postgres.stop()
        minio.stop()


async def upload_file(test_client: AsyncClient, relative_path: str, file_content: bytes) -> None:
    files = {"file": ("testfile.md", file_content, "text/markdown")}
    response = await test_client.put(f"/api/v1/files/{relative_path}", files=files)
    assert response.status_code == 201
    assert response.headers["Location"] == f"/files/{relative_path}"


async def get_explorer(client: AsyncClient)-> list[ApiDocumentSnippet]:
    result = await client.get("/api/v1/explorer")
    json = result.json()
    explorer = ApiExplorer.model_validate(json)
    return explorer.documents


def parse_event(event: str) -> Tuple[str, ApiDocumentSnippet | ApiDocumentDelete]:
    # Split into lines and extract event type and data
    lines = event.split("\n")
    event_type = lines[0].split(": ")[1]
    data = lines[1].split(": ")[1]
    
    if event_type == "delete":
        return event_type, ApiDocumentDelete.model_validate_json(data)
    else:
        return event_type, ApiDocumentSnippet.model_validate_json(data)



async def listen_docs(client: AsyncClient, nb_events: int) -> list[Tuple[str, ApiDocumentSnippet | ApiDocumentDelete]]:
    response = await client.get("/api/v1/document_events", params={"nb_events": nb_events})
    assert response.status_code == 200
    events: list[Tuple[str, ApiDocumentSnippet | ApiDocumentDelete]] = []
    for sse_line in response.text.split("\n\n"):
        if sse_line.startswith("event: "):
            event_type, event_data = parse_event(sse_line)
            events.append((event_type, event_data))
    return events


@pytest.mark.anyio
async def test_upload_file(test_client: AsyncClient) -> None:

    print("test_upload_file")
    # check the file does not exists already
    docs = await get_explorer(test_client)
    assert len(docs) == 0

    task = asyncio.create_task(listen_docs(test_client, 3))
    await asyncio.sleep(0)
    await upload_file(test_client, "test/path/to/file.md", b"This is a test file content")
    await asyncio.sleep(5)
    result = await task
    assert len(result) == 3
    assert result[0][0] == "insert"




# other test cases:
# - update with same source_version does nothing
# - update with different source_version but same hash only parse
# - update with different hash re-index correctly, previous file can still be queried
# - several indexer versions can work concurently
