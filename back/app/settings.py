from typing import Annotated
from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    seemantic_drive_root: str

    model_config = SettingsConfigDict(env_file=".env.dev")


@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore


RouteSettings = Annotated[Settings, Depends(get_settings)]