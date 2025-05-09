from pydantic_settings import BaseSettings

from common.db_service import DbSettings
from common.embedding_service import EmbeddingSettings
from common.minio_service import MinioSettings
from common.vector_db import LanceDbSettings


class CommonSettings(BaseSettings):
    minio: MinioSettings
    lance_db: LanceDbSettings
    db: DbSettings
    log_level: str
    indexer_version: int
    embedding: EmbeddingSettings
    embedding__litellm_api_key: str  # flattened becayse nested settings are not supported if it comes from secrets_dir

