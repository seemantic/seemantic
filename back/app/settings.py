from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    seemantic_drive_root: str
    # frozen=True makes it hashable so it can be used as an argument of other functions decorated with lru_cache
    model_config = SettingsConfigDict(env_file=".env.dev", frozen=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
