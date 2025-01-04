import logging
from typing import cast
from uuid import UUID

from common.document import ParsableFileType, is_parsable
from pydantic import BaseModel
from xxhash import xxh3_128_hexdigest

from common.db_service import DbService
from common.embedding_service import EmbeddingService
from indexer.chunker import Chunker
from indexer.parser import Parser
from indexer.settings import Settings
from indexer.source import Source, SourceDeleteEvent, SourceDocument, SourceUpsertEvent
from indexer.sources.seemantic_drive import SeemanticDriveSource


class RawDocIndexationResult(BaseModel):
    raw_content_hash: str


class Indexer:

    source: Source
    db: DbService
    parser: Parser = Parser()
    chunker: Chunker = Chunker()
    embedder: EmbeddingService

    def __init__(self, settings: Settings) -> None:
        self.source = SeemanticDriveSource(settings=settings.minio)
        self.db = DbService(settings.db)
        self.embedder = EmbeddingService(token=settings.jina_token)

    async def index(self, source_doc: SourceDocument, _raw_id: UUID) -> str:
        filetype = cast(ParsableFileType, source_doc.filetype)
        parsed = self.parser.parse(filetype, source_doc.content)
        chunks = self.chunker.chunk(parsed.markdown_content)
        _ = await self.embedder.embed_passage([chunk.content for chunk in chunks])

        raise NotImplementedError

    async def _reindex_and_store(self, uri: str) -> None:
        source_doc = await self.source.get_document(uri)
        if source_doc is None:
            logging.warning(f"Document {uri} not found in source")
            return
        if not is_parsable(source_doc.filetype):
            logging.warning(f"Unsupported file type {source_doc.filetype}")
            return

        raw_id = await self.db.upsert_source_document(uri, source_doc.raw_content_hash, source_doc.crawling_datetime)
        # Do indexation
        parsed_doc = await self.index(source_doc, raw_id)
        _ = await self.db.create_indexed_document(raw_id, xxh3_128_hexdigest(parsed_doc))

    async def start(self) -> None:

        uris_in_source = await self.source.all_uris()
        for uri in uris_in_source:
            await self._reindex_and_store(uri)

        # Delete documents not in source anymore
        db_docs = await self.db.get_all_source_documents()
        uris_in_db = {doc.source.source_uri for doc in db_docs}

        deleted_uris = uris_in_db - set(uris_in_source)
        await self.db.delete_source_documents(list(deleted_uris))

        async for doc_event in self.source.listen():
            if isinstance(doc_event, SourceDeleteEvent):
                await self.db.delete_source_documents([doc_event.uri])
            else:
                assert isinstance(doc_event, SourceUpsertEvent)
                await self._reindex_and_store(doc_event.uri)
