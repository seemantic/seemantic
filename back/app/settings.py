from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class MinioSettings(BaseModel, frozen=True):
    endpoint: str
    access_key: str
    secret_key: str


class Settings(BaseSettings):
    minio: MinioSettings
    seemantic_drive_root: str
    log_level: str

    # frozen=True makes it hashable so it can be used as an argument of other functions decorated with lru_cache
    model_config = SettingsConfigDict(env_file=".env.dev", frozen=True, env_nested_delimiter="__")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[reportCallIssue]


DepSettings = Annotated[Settings, Depends(get_settings)]
