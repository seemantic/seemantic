import logging
from typing import Set, cast
from uuid import UUID

import asyncio
from pydantic import BaseModel

from common.db_service import DbService
from common.document import IndexingStatus, ParsableFileType, ParsedDocument, is_parsable
from common.embedding_service import EmbeddingService
from common.vector_db import VectorDB
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
    vector_db: VectorDB
    uris_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=10000)
    uris_in_queue: Set[str] = set()

    def __init__(self, settings: Settings) -> None:
        self.embedder = EmbeddingService(token=settings.jina_token)
        self.vector_db = VectorDB(settings.minio, self.embedder.distance_metric())
        self.source = SeemanticDriveSource(settings=settings.minio)
        self.db = DbService(settings.db)

    async def _init(self) -> None:
        await self.vector_db.connect()
        asyncio.create_task(self.process_queue())

    async def process_queue(self):
        while True:
            uri = await self.uris_queue.get()
            self.uris_in_queue.remove(uri)
            await self._reindex_and_store(uri)
            self.uris_queue.task_done()



    async def index(self, source_doc: SourceDocument, _raw_id: UUID) -> ParsedDocument:
        filetype = cast(ParsableFileType, source_doc.filetype)
        parsed = self.parser.parse(filetype, source_doc.content)
        chunks = self.chunker.chunk(parsed)
        embedded_chunks = await self.embedder.embed_document(parsed, chunks)
        await self.vector_db.index(parsed, embedded_chunks)
        return parsed

    async def set_status(self, uri: str, status: IndexingStatus) -> None:
        pass

    async def _reindex_and_store(self, uri: str) -> None:
        source_doc = await self.source.get_document(uri)
        if source_doc is None:
            logging.warning(f"Document {uri} not found in source")
            return
        if not is_parsable(source_doc.filetype):
            # manage not parsable so it's still displayed in the UI ?
            logging.warning(f"Unsupported file type {source_doc.filetype}")
            return

        raw_id = await self.db.upsert_source_document(uri, source_doc.raw_content_hash, source_doc.crawling_datetime)
        # Do indexation
        parsed_doc = await self.index(source_doc, raw_id)
        _ = await self.db.create_indexed_document(raw_id, parsed_doc.hash)


    async def set_waiting_indexing(self, uris: list[str]):
        pass

    async def enqueue_uris(self, uris: list[str]) -> None:
        await self.set_waiting_indexing(uris)
        for uri in uris:
            self.uris_in_queue.add(uri) # when uri is added to queue, unique set should already be updated (so it can be removed)
            self.uris_queue.put_nowait(uri)

    async def start(self) -> None:

        await self._init()

        uris_in_source = await self.source.all_uris()
        await self.enqueue_uris(uris_in_source)

        # Delete documents not in source anymore
        db_docs = await self.db.get_all_source_documents()
        uris_in_db = {doc.source_document_uri for doc in db_docs}

        deleted_uris = uris_in_db - set(uris_in_source)
        await self.db.delete_source_documents(list(deleted_uris))

        async for doc_event in self.source.listen():
            if isinstance(doc_event, SourceDeleteEvent):
                await self.db.delete_source_documents([doc_event.uri])
            else:
                assert isinstance(doc_event, SourceUpsertEvent)
                if doc_event.uri in self.uris_in_queue: # if it's in queue, status is already set to waiting
                    continue
                await self.enqueue_uris([doc_event.uri])
                await self._reindex_and_store(doc_event.uri)






    