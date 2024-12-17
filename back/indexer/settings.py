from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from common.minio_service import MinioSettings


class Settings(BaseSettings):
    minio: MinioSettings
    seemantic_drive_root: str
    log_level: str

    # frozen=True makes it hashable so it can be used as an argument of other functions decorated with lru_cache
    model_config = SettingsConfigDict(env_file=".env.indexer.dev", frozen=True, env_nested_delimiter="__")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[reportCallIssue]
