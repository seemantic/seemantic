import lancedb  # pyright: ignore[reportMissingTypeStubs]
from lancedb import AsyncConnection  # pyright: ignore[reportMissingTypeStubs]
from lancedb.pydantic import LanceModel, Vector  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]
from pydantic import BaseModel

from common.document import Chunk, EmbeddedChunk, ParsedDocument
from common.minio_service import MinioSettings


class ChunkResult(BaseModel):
    chunk: Chunk
    score: float


class DocumentResult(BaseModel):
    parsed_document: ParsedDocument
    chunk_results: list[ChunkResult]


class Content(LanceModel):
    movie_id: int
    vector: Vector(128)  # type: ignore[FixedSizeListMixin]
    genres: str
    title: str
    imdb_id: int

    @property
    def imdb_url(self) -> str:
        return f"https://www.imdb.com/title/tt{self.imdb_id}"


class VectorDB:

    # Set the envvar AWS_ENDPOINT to the URL of your MinIO API
    # Set the envvars AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY with your MinIO credential
    # Call lancedb.connect("s3://minio_bucket_name")

    _settings: MinioSettings
    _db: AsyncConnection

    def __init__(self, settings: MinioSettings) -> None:
        self._settings = settings

    async def connect(self) -> None:
        protocol = "https" if self._settings.use_tls else "http"
        self._db = await lancedb.connect_async(
            f"s3://{self._settings.bucket}/lancedb",
            storage_options={
                "access_key_id": self._settings.access_key,
                "secret_access_key": self._settings.secret_key,
                "endpoint": f"{protocol}://{self._settings.endpoint}",
                "allow_http": f"{not self._settings.use_tls}",
            },
        )

        _ = await self._db.create_table(  # pyright: ignore[reportUnknownMemberType]
            "my_table_async",
            exist_ok=True,
            schema=Content,
        )

    async def query(self, vector: list[float]) -> list[DocumentResult]:
        raise NotImplementedError

    async def index(self, document: ParsedDocument, chunks: list[EmbeddedChunk]) -> None:
        raise NotImplementedError
