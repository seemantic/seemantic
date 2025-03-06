# pyright: strict, reportMissingTypeStubs=false
from sklearn import base
from testcontainers.postgres import PostgresContainer
from testcontainers.minio import MinioContainer
from fastapi.testclient import TestClient
from app.settings import Settings as AppSettings
from common.db_service import DbSettings
from common.minio_service import MinioSettings
from indexer.indexer import Indexer
from indexer.settings import get_settings
import pytest
import os
from main import app





@pytest.fixture(scope="session")
def test_client():
    with PostgresContainer("postgres:latest", driver="asyncpg") as postgres, MinioContainer() as minio:  # Ensure you use the correct version
        postgres.with_volume_mapping(os.path.abspath("/home/nicolas/dev/seemantic/back/postgres_db/sql_init/"), "/docker-entrypoint-initdb.d/")
        postgres.start()

        minio.start()

        def get_app_settings():
            base_settings = AppSettings()  # type: ignore[reportCallIssue]
            return AppSettings(
                **base_settings.model_dump(),
                db=DbSettings(username=postgres.username, password=postgres.password, host="localhost", port=postgres.port, database=postgres.dbname),
                minio=MinioSettings(endpoint="localhost", access_key=minio.access_key, secret_key=minio.secret_key, use_tls=False, bucket="seemantic_test_bucket"),
            )

        app.dependency_overrides[get_settings] = get_app_settings
        client = TestClient(app)

        yield client



def test_happy_path(test_client: TestClient) -> None:
    result = test_client.get("/explorer")
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
