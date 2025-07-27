import asyncio
import logging
from collections.abc import AsyncGenerator, Generator
from datetime import timedelta
from io import BytesIO
from typing import Any

from pydantic import BaseModel
from urllib3 import BaseHTTPResponse

from minio import Minio, S3Error

logging = logging.getLogger(__name__)


class MinioSettings(BaseModel, frozen=True):
    endpoint: str
    access_key: str
    secret_key: str
    use_tls: bool
    bucket: str


class MinioObject(BaseModel, frozen=True):
    key: str
    etag: str


class MinioObjectContent(BaseModel, frozen=True, arbitrary_types_allowed=True):
    object: MinioObject
    content: BytesIO


class PutMinioEvent(BaseModel, frozen=True):
    object: MinioObject


class DeleteMinioEvent(BaseModel, frozen=True):
    key: str


class MinioService:
    _minio_client: Minio
    _bucket_name: str
    _exit_subscription: bool = False

    def __init__(self, settings: MinioSettings) -> None:
        self._minio_client = Minio(
            settings.endpoint,
            access_key=settings.access_key,
            secret_key=settings.secret_key,
            secure=settings.use_tls,
        )

        self._bucket_name = settings.bucket

        if not self._minio_client.bucket_exists(self._bucket_name):
            self._minio_client.make_bucket(self._bucket_name)

    def _get_event(self, event: dict[str, Any]) -> Generator[PutMinioEvent | DeleteMinioEvent, None, None]:
        for record in event["Records"]:
            key: str = str(record["s3"]["object"]["key"])
            event_name: str = str(record["eventName"])
            if event_name.startswith(
                "s3:ObjectCreated:",
            ):  # deal with :Put, :Copy, :Post, :CompleteMultipartUpload
                etag: str = str(record["s3"]["object"]["eTag"])
                yield PutMinioEvent(object=MinioObject(key=key, etag=etag))
            elif event_name == "s3:ObjectRemoved:Delete":
                yield DeleteMinioEvent(key=key)

    async def async_listen_notifications(self, prefix: str) -> AsyncGenerator[PutMinioEvent | DeleteMinioEvent, None]:
        loop = asyncio.get_running_loop()
        while True:
            try:
                with self._minio_client.listen_bucket_notification(
                    bucket_name=self._bucket_name,
                    prefix=prefix,
                    events=("s3:ObjectCreated:*", "s3:ObjectRemoved:*"),
                ) as events:
                    event = await loop.run_in_executor(None, next, events)
                    my_events = self._get_event(event)
                    for my_event in my_events:
                        yield my_event
            except asyncio.CancelledError:
                break
            except StopIteration:
                break
            except Exception as e:  # noqa: BLE001
                logging.warning(f"Error: {e}, Reconnecting in 5 seconds...")
                await asyncio.sleep(5)  # Wait before reconnecting

    def create_or_update_document(self, key: str, file: BytesIO) -> None:
        self._minio_client.put_object(
            self._bucket_name,
            key,
            file,
            len(file.getbuffer()),
        )


    def get_document(self, object_name: str) -> MinioObjectContent | None:
        file: BaseHTTPResponse | None = None
        try:
            file = self._minio_client.get_object(
                self._bucket_name,
                object_name=object_name,
            )
            # header contains double quotes around the etag
            etag = str(file.headers.get("ETag")).strip('"')
            file_stream = BytesIO(file.read())
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            raise
        else:
            return MinioObjectContent(object=MinioObject(key=object_name, etag=etag), content=file_stream)
        finally:
            if file:
                file.close()
                file.release_conn()

    def get_all_documents(self, prefix: str) -> list[MinioObject]:
        return [
            MinioObject(key=str(obj.object_name), etag=str(obj.etag))
            for obj in self._minio_client.list_objects(
                self._bucket_name,
                recursive=True,
                prefix=prefix,
            )
        ]

    def delete_document(self, key: str) -> None:
        self._minio_client.remove_object(self._bucket_name, key)

    def get_presigned_url_for_upload(self, key: str) -> str:
        return self._minio_client.presigned_put_object(
            self._bucket_name,
            key,
            expires=timedelta(seconds=300),
        )

    def get_presigned_url_for_download(self, key: str) -> str:
        return self._minio_client.presigned_get_object(
            self._bucket_name,
            key,
            expires=timedelta(seconds=300),
        )

