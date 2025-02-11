# pyright: strict, reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from typing import cast

import lancedb
import pyarrow as pa
from lancedb import AsyncConnection
from pydantic import BaseModel
from xxhash import xxh3_128_hexdigest

from common.document import Chunk, EmbeddedChunk, ParsedDocument
from common.embedding_service import DistanceMetric
from common.minio_service import MinioSettings


class ChunkResult(BaseModel):
    chunk: Chunk
    distance: float


class ParsedDocumentResult(BaseModel):
    parsed_document: ParsedDocument
    chunk_results: list[ChunkResult]


row_parsed_content_hash = "parsed_content_hash"
row_str_content = "str_content"

row_start_index_in_doc = "start_index_in_doc"
row_end_index_in_doc = "end_index_in_doc"

parsed_doc_table_schema = pa.schema(
    [
        (row_parsed_content_hash, pa.string()),
        (row_str_content, pa.string()),
    ],
)

embedding_dim = 1024
chunk_table_schema = pa.schema(
    [
        (lancedb.common.VECTOR_COLUMN_NAME, pa.list_(pa.float16(), embedding_dim)),
        (row_parsed_content_hash, pa.string()),
        (row_start_index_in_doc, pa.int64()),
        (row_end_index_in_doc, pa.int64()),
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
    distance_metric: str

    def __init__(self, settings: MinioSettings, distance_metric: DistanceMetric) -> None:
        self._settings = settings
        self.distance_metric = distance_metric

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
            mode="overwrite",  # For now as we test, this should be removed after
        )

        self._chunk_table = await self._db.create_table(
            chunk_table_name,
            exist_ok=True,
            schema=chunk_table_schema,
            enable_v2_manifest_paths=True,
            mode="overwrite",  # For now as we test, this should be removed after
        )

    async def query(self, vector: list[float], nb_chunks_to_retrieve: int) -> list[ParsedDocumentResult]:

        chunk_table: pa.Table = (
            await self._chunk_table.query()
            .nearest_to(vector)
            .distance_type(self.distance_metric)
            .column(lancedb.common.VECTOR_COLUMN_NAME)
            .limit(nb_chunks_to_retrieve)
            .to_arrow()
        )
        parsed_doc_hashes = cast(set[str], set(chunk_table[row_parsed_content_hash].to_pylist()))
        sql_in_str = ",".join([f"'{parsed_doc_hash}'" for parsed_doc_hash in parsed_doc_hashes])

        parsed_table = (
            await self._parsed_doc_table.query().where(f"{row_parsed_content_hash} IN ({sql_in_str})").to_arrow()
        )

        # Convert to Pandas for fast groupby operations
        parsed_df = parsed_table.to_pandas()
        chunk_df = chunk_table.to_pandas()

        # Group chunks by parsed_content_hash (avoids repeated filtering)
        chunk_groups = chunk_df.groupby(row_parsed_content_hash)

        # Build results using dictionary lookups
        results = []

        for _, parsed_row in parsed_df.iterrows():
            parsed_hash = cast(str, parsed_row[row_parsed_content_hash])
            content = cast(str, parsed_row[row_str_content])
            parsed_doc = ParsedDocument(markdown_content=content)

            # Retrieve chunks efficiently using groupby dictionary
            chunk_results = [
                ChunkResult(
                    chunk=Chunk(
                        start_index_in_doc=cast(int, chunk_row[row_start_index_in_doc]),
                        end_index_in_doc=cast(int, chunk_row[row_end_index_in_doc]),
                    ),
                    distance=cast(float, chunk_row["_distance"]),  # Placeholder for distance computation
                )
                for _, chunk_row in chunk_groups.get_group(parsed_hash).iterrows()
            ]

            results.append(ParsedDocumentResult(parsed_document=parsed_doc, chunk_results=chunk_results))

        return results

    async def is_indexed(self, document: ParsedDocument) -> bool:
        parsed_hash = xxh3_128_hexdigest(document.markdown_content)
        # we check _chunk_table as it is created last after _parsed_doc_table (and deleted first)
        nb_rows = await self._chunk_table.count_rows(f"{row_parsed_content_hash} = '{parsed_hash}'")
        return nb_rows > 0

    async def index(self, document: ParsedDocument, chunks: list[EmbeddedChunk]) -> str:
        content_array = pa.array([document.markdown_content])
        parsed_content_hash = xxh3_128_hexdigest(document.markdown_content)
        parsed_content_hash_array = pa.array([parsed_content_hash])
        doc_table = pa.Table.from_arrays(
            [parsed_content_hash_array, content_array],
            schema=parsed_doc_table_schema,
        )
        await self._parsed_doc_table.merge_insert(
            row_parsed_content_hash,
        ).when_not_matched_insert_all().when_not_matched_by_source_delete(
            f"{row_parsed_content_hash} = '{parsed_content_hash}'",
        ).execute(
            doc_table,
        )

        embedding_array = pa.array([c.embedding.embedding for c in chunks])
        parsed_content_hash_array_chunk_table: pa.StringArray = pa.array([parsed_content_hash] * len(chunks))
        start_index_array = pa.array([c.chunk.start_index_in_doc for c in chunks])
        end_index_array = pa.array([c.chunk.end_index_in_doc for c in chunks])
        chunk_table = pa.Table.from_arrays(
            [embedding_array, parsed_content_hash_array_chunk_table, start_index_array, end_index_array],
            schema=chunk_table_schema,
        )

        await self._chunk_table.merge_insert(
            row_parsed_content_hash,
        ).when_not_matched_insert_all().when_not_matched_by_source_delete(
            f"{row_parsed_content_hash} = '{parsed_content_hash}'",
        ).execute(
            chunk_table,
        )
        return parsed_content_hash
        # indexing is not necessary up to 100k rows. cf. https://lancedb.github.io/lancedb/ann_indexes/#when-is-it-necessary-to-create-an-ann-vector-index
