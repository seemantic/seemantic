from pydantic_settings import BaseSettings

from common.db_service import DbSettings
from common.minio_service import MinioSettings
from common.vector_db import LanceDbSettings


class CommonSettings(BaseSettings):
    minio: MinioSettings
    lance_db: LanceDbSettings
    db: DbSettings
    log_level: str
    jina_token: str
    indexer_version: int
