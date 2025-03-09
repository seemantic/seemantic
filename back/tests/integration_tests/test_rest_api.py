# pyright: strict, reportMissingTypeStubs=false
import asyncio
from typing import Generator, AsyncGenerator
from testcontainers.postgres import PostgresContainer
from testcontainers.minio import MinioContainer
from fastapi.testclient import TestClient
from app.settings import Settings as AppSettings, get_settings as get_app_settings
from indexer.settings import Settings as IndexerSettings
from common.db_service import DbSettings
from common.minio_service import MinioSettings
from indexer.indexer import Indexer
import pytest
import os
from main import app
import pytest_asyncio

@pytest_asyncio.fixture(scope="session")
async def test_client() -> AsyncGenerator[TestClient, None]:
    postgres = PostgresContainer("postgres:17", driver="asyncpg")
    minio: MinioContainer = MinioContainer()
    postgres.with_volume_mapping(os.path.abspath("/home/nicolas/dev/seemantic/back/postgres_db/sql_init/"), "/docker-entrypoint-initdb.d/")
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
        database=postgres.dbname)

    minio_settings = MinioSettings(
        endpoint=minio_endpoint,
        access_key=minio.access_key,
        secret_key=minio.secret_key,
        use_tls=False,
        bucket="seemantic-test"
    )

    def get_test_app_settings():
        base_settings = AppSettings()  # type: ignore[reportCallIssue]
        settings_dict = base_settings.model_dump()
        settings_dict["db"] = db_settings
        settings_dict["minio"] = minio_settings
        return AppSettings(**settings_dict)
    
    def get_test_indexer_settings():
        base_settings = IndexerSettings()  # type: ignore[reportCallIssue]
        settings_dict = base_settings.model_dump()
        settings_dict["db"] = db_settings
        settings_dict["minio"] = minio_settings
        return IndexerSettings(**settings_dict)

    app.dependency_overrides[get_app_settings] = get_test_app_settings
    client = TestClient(app)
    
    indexer = Indexer(get_test_indexer_settings())
    asyncio.create_task(indexer.start())
    await asyncio.sleep(5)
    yield client
    postgres.stop()
    minio.stop()



@pytest.mark.asyncio
async def test_happy_path(test_client: TestClient) -> None:
    relative_path = "test/path/to/file"
    file_content = b"This is a test file content"
    files = {"file": ("testfile.txt", file_content, "text/plain")}

    # Make a PUT request to the endpoint
    response = test_client.put(f"/api/v1/files/{relative_path}", files=files)

    result = test_client.get("/api/v1/explorer")
    print(result.json())
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
    assert True
    #response = test_client.get("/health")  # Replace with your actual health check endpoint
    #assert response.status_code == 200
    #assert response.json()["database"] == "ok"


def test_indexer_restart() -> None:
    pass


def test_server_restart() -> None:
    pass


def test_unparsable_file() -> None:
    pass


def test_hug_file() -> None:
    pass
