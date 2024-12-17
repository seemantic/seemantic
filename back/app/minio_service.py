from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.settings import DepSettings
from common.minio_service import MinioService


@lru_cache
def get_minio_service(settings: DepSettings) -> MinioService:
    return MinioService(settings=settings.minio)


DepMinioService = Annotated[MinioService, Depends(get_minio_service)]
