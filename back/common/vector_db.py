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



    def __init__(self, settings: MinioSettings) -> None:

        self.db = lancedb.connect(
            "s3://seemantic_vector_db",
            storage_options={
        "aws_access_key_id": settings.access_key,
        "aws_secret_access_key": settings.secret_key,
        "aws_endpoint": settings.endpoint
    })
        
    def query(self, vector: list[float]) -> list[DocumentResult]:
        raise NotImplementedError

    def index(self, document: ParsedDocument, chunks: list[EmbeddedChunk]) -> None:
        raise NotImplementedError
