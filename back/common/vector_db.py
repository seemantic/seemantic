# pyright: strict, reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
import lancedb
import pyarrow as pa
from lancedb import AsyncConnection
from pydantic import BaseModel

from common.document import Chunk, EmbeddedChunk, ParsedDocument
from common.minio_service import MinioSettings


class ChunkResult(BaseModel):
    chunk: Chunk
    score: float


class DocumentResult(BaseModel):
    parsed_document: ParsedDocument
    chunk_results: list[ChunkResult]


parsed_doc_table_schema = pa.schema(
    [
        ("parsed_doc_hash", pa.string()),
        ("str_content", pa.string()),
    ],
)

embedding_dim = 1024
chunk_table_schema = pa.schema(
    [
        ("embedding", pa.list_(pa.float16(), embedding_dim)),
        ("parsed_doc_hash", pa.string()),
        ("start_index_in_doc", pa.int64()),
        ("end_index_in_doc", pa.int64()),
    ],
)
parsed_doc_table_version = "v1"
chunk_table_version = "v1"


parsed_doc_table_name = f"parsed_doc_{parsed_doc_table_version}"
chunk_table_name = f"chunk_{chunk_table_version}"

class VectorDB:

    _settings: MinioSettings
    _db: AsyncConnection
    _parsed_doc_table: lancedb.AsyncTable
    _chunk_table: lancedb.AsyncTable

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

        self._parsed_doc_table = await self._db.create_table(
            parsed_doc_table_name,
            exist_ok=True,
            schema=parsed_doc_table_schema,
            enable_v2_manifest_paths=True,
            
            mode="overwrite" # For now as we test, this should be removed after
        )

        self._chunk_table = await self._db.create_table(
            chunk_table_name,
            exist_ok=True,
            schema=chunk_table_schema,
            enable_v2_manifest_paths=True,
            mode="overwrite" # For now as we test, this should be removed after
        )

    async def query(self, vector: list[float]) -> list[DocumentResult]:
        raise NotImplementedError

    async def index(self, document: ParsedDocument, chunks: list[EmbeddedChunk]) -> None:
        data = [document.compute_hash(), document.markdown_content]
        await self._parsed_doc_table.add(data)

        data = [[
            chunk.embedding.embedding,
            document.compute_hash(),
            chunk.chunk.start_index_in_doc,
            chunk.chunk.end_index_in_doc,
        ] for chunk in chunks]
        await self._chunk_table.add(data)
