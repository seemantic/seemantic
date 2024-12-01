# test upload_file
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.settings import Settings, get_settings
from main import app

client = TestClient(app)


def get_settings_override() -> Settings:
    return Settings(seemantic_drive_root="tests/.generated/seemantic_drive")


# remove generated files before each test
@pytest.fixture(autouse=True)
def _cleanup() -> None:  # pyright: ignore[reportUnusedFunction]
    shutil.rmtree("tests/.generated/", ignore_errors=True)


@pytest.fixture()
def store_file_on_semantic_drive() -> str:
    dest_relative_path = "relative_dir/dest_file.txt"
    dest_full_path = f"{get_settings_override().seemantic_drive_root}/{dest_relative_path}"
    Path(dest_full_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile("./tests/existing_file_in_drive.txt", dest_full_path)
    return dest_relative_path


app.dependency_overrides[get_settings] = get_settings_override


# Business spec:
# - upload a file
# - delete a file
# - get a file
# - get file snippets

# Technical specs
# - upload file, is indexed
# - upload file with same path, replace previous
# - delete file existing, not indexed anymore
# - delete file not existing, do nothing


def test_upsert_file_on_new_path() -> None:

    dest_relative_path = "new_dir/test_upsert_file_on_new_path.txt"
    origin_path = "./tests/to_upload.txt"

    with Path(origin_path).open("rb") as origin_file:
        response = client.put(f"/api/v1/files/{dest_relative_path}", files={"file": origin_file})
        assert response.headers["Location"] == f"/files/{dest_relative_path}"
        assert response.status_code == 201
        full_dest_path = f"{get_settings_override().seemantic_drive_root}/{dest_relative_path}"
        assert Path(full_dest_path).read_text() == "to_upload"


def test_upsert_file_on_existing_path(store_file_on_semantic_drive: str) -> None:
    origin_path = "./tests/to_replace.txt"
    with Path(origin_path).open("rb") as origin_file:
        response = client.put(f"/api/v1/files/{store_file_on_semantic_drive}", files={"file": origin_file})
        assert response.headers["Location"] == f"/files/{store_file_on_semantic_drive}"
        assert response.status_code == 201
        full_dest_path = f"{get_settings_override().seemantic_drive_root}/{store_file_on_semantic_drive}"
        assert Path(full_dest_path).read_text() == "to_replace"


def test_get_file(store_file_on_semantic_drive: str) -> None:
    response = client.get(f"/api/v1/files/{store_file_on_semantic_drive}")
    assert response.status_code == 200
    assert response.content.decode("utf-8") == "existing_file_in_drive"


def test_get_file_without_file() -> None:
    response = client.get("/api/v1/files/this_file_does_not_exist.txt")
    assert response.status_code == 404


def test_delete_file(store_file_on_semantic_drive: str) -> None:
    response = client.delete(f"/api/v1/files/{store_file_on_semantic_drive}")
    assert response.status_code == 204
    assert not Path(f"{get_settings_override().seemantic_drive_root}/{store_file_on_semantic_drive}").exists()


def test_delete_file_without_file() -> None:
    response = client.delete("/api/v1/files/this_file_does_not_exist.txt")
    assert response.status_code == 204
