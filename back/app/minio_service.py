from functools import lru_cache
from io import BytesIO
from typing import Annotated

from fastapi import Depends
from urllib3 import BaseHTTPResponse

from app.settings import DepSettings, MinioSettings
from minio import Minio, S3Error


class MinioService:

    _minio_client: Minio
    _bucket_name = "seemantic"
    _semantic_drive_prefix = "seemantic_drive"

    def _get_seemantic_drive_object_name(self, relative_path: str) -> str:
        return f"{self._semantic_drive_prefix}/{relative_path}"

    def __init__(self, settings: MinioSettings) -> None:
        self._minio_client = Minio(
            settings.endpoint,
            access_key=settings.access_key,
            secret_key=settings.secret_key,
            secure=False,
        )

        if not self._minio_client.bucket_exists(self._bucket_name):
            self._minio_client.make_bucket(self._bucket_name)

    def create_or_update_document(self, relative_path: str, file: BytesIO) -> None:
        self._minio_client.put_object(
            self._bucket_name,
            self._get_seemantic_drive_object_name(relative_path),
            file,
            len(file.getbuffer()),
        )

    def get_file(self, relative_path: str) -> BytesIO | None:

        file: BaseHTTPResponse | None = None
        try:
            file = self._minio_client.get_object(
                self._bucket_name,
                self._get_seemantic_drive_object_name(relative_path),
            )
            file_stream = BytesIO(file.read())
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            raise
        else:
            return file_stream
        finally:
            if file:
                file.close()
                file.release_conn()

    def get_files(self) -> list[str]:
        return [
            str(obj.object_name)
            for obj in self._minio_client.list_objects(
                self._bucket_name,
                recursive=True,
                prefix=f"{self._semantic_drive_prefix}/",
            )
        ]

    def delete_document(self, relative_path: str) -> None:
        self._minio_client.remove_object(self._bucket_name, self._get_seemantic_drive_object_name(relative_path))


@lru_cache
def get_minio_service(settings: DepSettings) -> MinioService:
    return MinioService(settings=settings.minio)


DepMinioService = Annotated[MinioService, Depends(get_minio_service)]
