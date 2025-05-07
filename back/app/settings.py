from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import SettingsConfigDict

from app.generator import GeneratorSettings
from common.settings import CommonSettings


class Settings(CommonSettings):
    generator: GeneratorSettings
    generator__litellm_api_key: str  # flattened becayse nested settings are not supported if it comes from secrets_dir

    # frozen=True makes it hashable so it can be used as an argument of other functions decorated with lru_cache
    model_config = SettingsConfigDict(
        env_file=".env.dev",
        frozen=True,
        env_nested_delimiter="__",
        secrets_dir=".ignored/secrets",
    )




@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[reportCallIssue]


DepSettings = Annotated[Settings, Depends(get_settings)]
