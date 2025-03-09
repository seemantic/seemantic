from functools import lru_cache

from pydantic_settings import SettingsConfigDict

from common.settings import CommonSettings


class Settings(CommonSettings):

    # frozen=True makes it hashable so it can be used as an argument of other functions decorated with lru_cache
    model_config = SettingsConfigDict(
        env_file=".env.indexer.dev",
        frozen=True,
        env_nested_delimiter="__",
        secrets_dir=".ignored/secrets",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[reportCallIssue]
