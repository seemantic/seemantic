# test upload_file
from pathlib import Path

from fastapi.testclient import TestClient

from main import app
from app.settings import Settings, get_settings

client = TestClient(app)


# TODO NICO Here
# check that the file is present and has been indexed (ask questions)
# after modification: check it's taken into account
# after deletion: check it's taken into account

def get_settings_override() -> Settings:
    return Settings(seemantic_drive_root="tests/.generated/seemantic_drive")


app.dependency_overrides[get_settings] = get_settings_override



def test_upload_file_index_it():
    
    # TODO NICO
    # ko if folder before dest_relative_path
    # ko if run at git root level instead of back (settings not found) -> OK ? Convention on run tout depuis back pour le dev du back ?
    #    
    dest_relative_path = "dest_name.txt"
    # get the file path, independently of the folder executing the pytest script
    origin_path = Path(__file__).parent / "test_file.txt"

    response = client.put(f"/api/v1/files/{dest_relative_path}", files={"file": open(origin_path, "rb")})
    assert response.status_code == 201

