# pyright: strict, reportMissingTypeStubs=false
from testcontainers.postgres import PostgresContainer
from testcontainers.minio import MinioContainer
from fastapi.testclient import TestClient
from app.settings import Settings as AppSettings, get_settings as get_app_settings
from common.db_service import DbSettings
from common.minio_service import MinioSettings
from indexer.indexer import Indexer
import pytest
import os
from main import app





@pytest.fixture(scope="session")
def test_client():
    postgres = PostgresContainer("postgres:17", driver="asyncpg")
    minio = MinioContainer()
    postgres.with_volume_mapping(os.path.abspath("/home/nicolas/dev/seemantic/back/postgres_db/sql_init/"), "/docker-entrypoint-initdb.d/")
    postgres.start()
    minio.start()

    def get_test_app_settings():
        base_settings = AppSettings()  # type: ignore[reportCallIssue]
        
        # Get the settings as a dictionary
        settings_dict = base_settings.model_dump()
        
        # Create new nested settings objects
        new_db = DbSettings(
            username=postgres.username,
            password=postgres.password,
            host="localhost",
            port=postgres.get_exposed_port(postgres.port),
            database=postgres.dbname
        )
        
        new_minio = MinioSettings(
            endpoint="localhost",
            access_key=minio.access_key,
            secret_key=minio.secret_key,
            use_tls=False,
            bucket="seemantic_test_bucket"
        )
        
        # Replace the nested settings in the dictionary
        settings_dict["db"] = new_db
        settings_dict["minio"] = new_minio
        
        # Create a new instance with the modified dictionary
        return AppSettings(**settings_dict)

    app.dependency_overrides[get_app_settings] = get_test_app_settings
    client = TestClient(app)

    yield client
    postgres.stop()
    minio.stop()




def test_happy_path(test_client: TestClient) -> None:
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
