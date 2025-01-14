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
        (lancedb.common.VECTOR_COLUMN_NAME, pa.list_(pa.float16(), embedding_dim)),
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
    nb_chunks_to_retrieve = 10

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

        chunk_results: pa.Table = await self._chunk_table.query().nearest_to(vector).limit(self.nb_chunks_to_retrieve).to_arrow()
        parsed_doc_hashes: set[str] = set(chunk_results["parsed_doc_hash"].to_pylist())
        sql_in_str = ",".join([f"'{hash}'" for hash in parsed_doc_hashes])

        parsed_docs = await self._parsed_doc_table.query().where(f"parsed_doc_hash IN ({sql_in_str})").to_arrow()

        hash_to_content: dict[str, str] = dict(zip(parsed_docs["parsed_doc_hash"].to_pylist(), parsed_docs["str_content"].to_pylist()))

        hash_to_chunks: dict[str, list[ChunkResult]] = {hash: [] for hash in parsed_doc_hashes}
        for chunk_row in chunk_results.to_pylist():
            hash_to_chunks[chunk_row["parsed_doc_hash"]].append(
                ChunkResult(chunk=Chunk(
                    start_index_in_doc=chunk_row["start_index_in_doc"],
                    end_index_in_doc=chunk_row["end_index_in_doc"],
                ), score=77)
        )
            
        return [
            DocumentResult(
                parsed_document=ParsedDocument(
                    markdown_content=hash_to_content[hash],
                ),
                chunk_results=chunks,
            )
            for hash, chunks in hash_to_chunks.items()
        ]

    async def index(self, document: ParsedDocument, chunks: list[EmbeddedChunk]) -> None:
        doc_hash: str = document.compute_hash()
        hash_array = pa.array([doc_hash])
        content_array = pa.array([document.markdown_content])
        doc_table = pa.Table.from_arrays([hash_array, content_array], schema=parsed_doc_table_schema)
        await self._parsed_doc_table.add(doc_table)

        embedding_array = pa.array([c.embedding.embedding for c in chunks])
        hash_array: pa.StringArray = pa.array([doc_hash]*len(chunks))
        start_index_array = pa.array([c.chunk.start_index_in_doc for c in chunks])
        end_index_array = pa.array([c.chunk.end_index_in_doc for c in chunks])
        chunk_table = pa.Table.from_arrays([embedding_array, hash_array, start_index_array, end_index_array], schema=chunk_table_schema) 

        await self._chunk_table.add(chunk_table)
        # indexing is not necessary up to 100k rows. cf. https://lancedb.github.io/lancedb/ann_indexes/#when-is-it-necessary-to-create-an-ann-vector-index
