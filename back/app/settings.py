from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.db_service import DbSettings
from common.minio_service import MinioSettings


class Settings(BaseSettings):
    minio: MinioSettings
    db: DbSettings
    seemantic_drive_root: str
    log_level: str

    # frozen=True makes it hashable so it can be used as an argument of other functions decorated with lru_cache
    model_config = SettingsConfigDict(env_file=".env.dev", frozen=True, env_nested_delimiter="__")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[reportCallIssue]


DepSettings = Annotated[Settings, Depends(get_settings)]
