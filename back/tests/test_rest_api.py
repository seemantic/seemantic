# test upload_file
from pathlib import Path

from fastapi.testclient import TestClient

from app.settings import Settings, get_settings
from main import app

client = TestClient(app)


def get_settings_override() -> Settings:
    return Settings(seemantic_drive_root="tests/.generated/seemantic_drive")


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


def test_upload_file() -> None:

    dest_relative_path = "relative_dir/dest_name.txt"
    # get the file path, independently of the folder executing the pytest script
    origin_path = "./tests/test_file.txt"

    with Path(origin_path).open("rb") as origin_file:
        response = client.put(f"/api/v1/files/{dest_relative_path}", files={"file": origin_file})
        assert response.headers["Location"] == f"/files/{dest_relative_path}"
        assert response.status_code == 201
        # check that the file is stored
        full_dest_path = f"{get_settings_override().seemantic_drive_root}/{dest_relative_path}"

        origin_file.seek(0)  # reset the cursor to the beginning to read it again (it's already read by client.put call)
        with Path(full_dest_path).open("rb") as dest_file:
            assert dest_file.read() == origin_file.read()
