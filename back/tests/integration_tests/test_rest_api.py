# pyright: strict, reportMissingTypeStubs=false
import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from testcontainers.minio import MinioContainer
from testcontainers.postgres import PostgresContainer

from app.settings import Settings as AppSettings
from app.settings import get_settings as get_app_settings
from common.db_service import DbSettings
from common.minio_service import MinioSettings
from indexer.indexer import Indexer
from indexer.settings import Settings as IndexerSettings
from main import app


@pytest_asyncio.fixture(scope="session")  # type: ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
async def test_client() -> AsyncGenerator[TestClient, None]:
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
    client = TestClient(app)

    indexer = Indexer(get_test_indexer_settings())
    indexed_task = asyncio.create_task(indexer.start())  # type: ignore[reportUnusedVariable]
    await asyncio.sleep(5)
    yield client
    indexed_task.cancel()
    postgres.stop()
    minio.stop()


def upload_file(test_client: TestClient, relative_path: str, file_content: bytes) -> None:
    files = {"file": ("testfile.txt", file_content, "text/plain")}
    response = test_client.put(f"/api/v1/files/{relative_path}", files=files)
    assert response.status_code == 201
    assert response.headers["Location"] == f"/files/{relative_path}"


@pytest.mark.asyncio
async def test_happy_path(test_client: TestClient) -> None:

    upload_file(test_client, "test/path/to/file.txt", b"This is a test file content")

    result = test_client.get("/api/v1/explorer")
    assert result is not None
    # - start the server
    # - start the indexed
    # 1) upload a new document
    # 2) create a query
    # 3) check the answer
    # 4) update the document
    # 5) ask the query again
    # 6) check the answer is updated
    # 7) delete the document
    # 8) ask the query again
    # 9) check the answer is deleted


def test_indexer_restart() -> None:
    pass


def test_server_restart() -> None:
    pass


def test_unparsable_file() -> None:
    pass


def test_hug_file() -> None:
    pass
