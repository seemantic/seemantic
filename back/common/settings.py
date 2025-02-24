from pydantic_settings import BaseSettings

from common.db_service import DbSettings
from common.minio_service import MinioSettings


class CommonSettings(BaseSettings):
    minio: MinioSettings
    db: DbSettings
    log_level: str
    jina_token: str
    indexer_version: int
