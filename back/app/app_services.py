from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.settings import DepSettings
from common.db_service import DbService
from common.minio_service import MinioService


@lru_cache
def get_minio_service(settings: DepSettings) -> MinioService:
    return MinioService(settings=settings.minio)


DepMinioService = Annotated[MinioService, Depends(get_minio_service)]


@lru_cache
def get_db_service(settings: DepSettings) -> DbService:
    return DbService(settings=settings.db)


DepDbService = Annotated[DbService, Depends(get_db_service)]
