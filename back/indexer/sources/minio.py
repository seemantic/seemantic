from collections.abc import AsyncGenerator

from common.minio_service import MinioService
from indexer.settings import MinioSettings
from indexer.source import DocumentEvent, Source


class MinioSource(Source):

    _settings: MinioSettings

    def __init__(self, settings: MinioSettings) -> None:
        self._minio_service = MinioService(settings=settings)

    def all_uris(self) -> list[str]:
        raise NotImplementedError("all_uris")

    def listen(self) -> AsyncGenerator[DocumentEvent]:

        raise NotImplementedError("start_minio")
