import lancedb

from pydantic import BaseModel
from common.minio_service import MinioSettings
from common.document import Chunk, EmbeddedChunk, ParsedDocument


class ChunkResult(BaseModel):
    chunk: Chunk
    score: float


class DocumentResult(BaseModel):
    parsed_document: ParsedDocument
    chunk_results: list[ChunkResult]


class VectorDB:

# Set the envvar AWS_ENDPOINT to the URL of your MinIO API
# Set the envvars AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY with your MinIO credential
# Call lancedb.connect("s3://minio_bucket_name")

    _settings: MinioSettings
    _db: lancedb.AsyncConnection

    def __init__(self, settings: MinioSettings) -> None:
        self._settings = settings

    async def connect(self) -> None:
        self._db = await lancedb.connect_async(
            "s3://seemantic/lancedb",
            storage_options={
        "aws_access_key_id": self._settings.access_key,
        "aws_secret_access_key": self._settings.secret_key,
        "aws_endpoint": "http://localhost:9000",
        "allow_http": "True"})
        
        data = [
    {"vector": [3.1, 4.1], "item": "foo", "price": 10.0},
    {"vector": [5.9, 26.5], "item": "bar", "price": 20.0},]

        async_tbl = await self._db.create_table("my_table_async", data=data)
        
    async def query(self, vector: list[float]) -> list[DocumentResult]:
        raise NotImplementedError()

    async def index(self, document: ParsedDocument, chunks: list[EmbeddedChunk]) -> None:
        raise NotImplementedError()


