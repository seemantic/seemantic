import lancedb
from lancedb import AsyncConnection
from lancedb.pydantic import Vector, LanceModel
from pydantic import BaseModel
from common.minio_service import MinioSettings
from common.document import Chunk, EmbeddedChunk, ParsedDocument


class ChunkResult(BaseModel):
    chunk: Chunk
    score: float


class DocumentResult(BaseModel):
    parsed_document: ParsedDocument
    chunk_results: list[ChunkResult]


class Content(LanceModel):
    movie_id: int
    vector: Vector(128)
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
        self._db = await lancedb.connect_async(
            f"s3://{self._settings.bucket}/lancedb",  # duplication from minio TODO
            storage_options={
                "aws_access_key_id": self._settings.access_key,
                "aws_secret_access_key": self._settings.secret_key,
                "aws_endpoint": f"http://{self._settings.endpoint}",  # maybe this should ref minio service instead of config directly ?
                "allow_http": f"{not self._settings.use_tls}",
            },
        )  # todo make it configurable

        async_tbl = await self._db.create_table("my_table_async", exist_ok=True, schema=Content)

    async def query(self, vector: list[float]) -> list[DocumentResult]:
        raise NotImplementedError()

    async def index(self, document: ParsedDocument, chunks: list[EmbeddedChunk]) -> None:
        raise NotImplementedError()
