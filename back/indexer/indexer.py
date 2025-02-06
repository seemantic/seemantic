from datetime import datetime
import datetime as dt
import logging
from typing import Set, cast

import asyncio
from pydantic import BaseModel

from common.utils import hash_file_content
from common.db_service import DbDocument, DbDocumentIndexedVersion, DbService, TableDocumentStatusEnum
from common.document import ParsableFileType, is_parsable
from common.embedding_service import EmbeddingService
from common.vector_db import VectorDB
from indexer.chunker import Chunker
from indexer.parser import Parser
from indexer.settings import Settings
from indexer.source import Source, SourceDeleteEvent, SourceDocument, SourceUpsertEvent, SourceDocumentReference
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
            self.uris_in_queue.remove(uri)  # uri can be re-added to queue as soon as processing starts
            await self._reindex_and_store(uri)
            self.uris_queue.task_done()

    async def index(self, source_doc: SourceDocument) -> str:
        filetype = cast(ParsableFileType, source_doc.filetype)
        raw_hash = hash_file_content(source_doc.content)
        parsed = self.parser.parse(filetype, source_doc.content)
        chunks = self.chunker.chunk(parsed)
        embedded_chunks = await self.embedder.embed_document(parsed, chunks)
        await self.vector_db.index(raw_hash, parsed, embedded_chunks)
        return raw_hash

    # TODO manage indexing in VS

    async def _reindex_and_store(self, uri: str) -> None:
        await self.db.update_documents_status([uri], TableDocumentStatusEnum.INDEXING, None)
        source_doc = await self.source.get_document(uri)
        if source_doc is None:
            logging.warning(f"Document {uri} not found in source")
            await self.db.update_documents_status(
                [uri], TableDocumentStatusEnum.INDEXING_ERROR, "Document not found in source"
            )
        elif not is_parsable(source_doc.filetype):
            # manage not parsable so it's still displayed in the UI ?
            logging.warning(f"Unsupported file type {source_doc.filetype}")
            await self.db.update_documents_status(
                [uri], TableDocumentStatusEnum.INDEXING_ERROR, f"Unsupported file type {source_doc.filetype}"
            )
        else:
            # Do indexation
            raw_hash = await self.index(source_doc)
            await self.db.update_documents_indexed_version(
                {
                    uri: DbDocumentIndexedVersion(
                        raw_hash=raw_hash,
                        source_version=source_doc.doc_ref.source_version_id,
                        last_modification=datetime.now(tz=dt.timezone.utc),
                    )
                }
            )

    async def enqueue_doc_refs(self, refs: list[SourceDocumentReference]) -> None:
        for ref in refs:
            self.uris_in_queue.add(
                ref.uri
            )  # when uri is added to queue, unique set should already be updated (so it can be removed)
            self.uris_queue.put_nowait(ref.uri)

    async def manage_upserts(self, refs: list[SourceDocumentReference], uri_to_db_docs: dict[str, DbDocument]):
        docs_to_index: list[SourceDocumentReference] = []
        docs_to_create: list[SourceDocumentReference] = []
        for doc_ref in refs:
            uri = doc_ref.uri
            if uri in self.uris_in_queue:
                continue
            db_doc = uri_to_db_docs.get(uri, None)
            if db_doc is None:
                docs_to_create.append(doc_ref)
            elif (
                db_doc.indexed_version is None
                or db_doc.indexed_version.source_version is None
                or doc_ref.source_version_id is None
                or db_doc.indexed_version.source_version != doc_ref.source_version_id
            ):
                # doc might have changed
                docs_to_index.append(doc_ref)
            else:
                # doc did not change since last successful indexing
                continue

        await self.db.create_documents([doc.uri for doc in docs_to_create])
        await self.db.update_documents_status([doc.uri for doc in docs_to_index], TableDocumentStatusEnum.PENDING, None)

        await self.enqueue_doc_refs(docs_to_index + docs_to_create)

    async def start(self) -> None:

        await self._init()

        source_doc_refs = await self.source.all_doc_refs()
        uri_to_doc_refs = {doc_ref.uri: doc_ref for doc_ref in source_doc_refs}
        db_docs = await self.db.get_all_documents()
        uri_to_db = {doc.uri: doc for doc in db_docs}

        await self.manage_upserts(source_doc_refs, uri_to_db)
        to_delete = set(uri_to_db.keys()) - set(uri_to_doc_refs.keys())
        await self.db.delete_documents(list(to_delete))

        async for event in self.source.listen():
            if isinstance(event, SourceUpsertEvent):
                uri_to_db = await self.db.get_documents([event.doc_ref.uri])
                await self.manage_upserts([event.doc_ref], uri_to_db)
            elif isinstance(event, SourceDeleteEvent):  # type: ignore
                await self.db.delete_documents([event.uri])


# on each source_ref received:
# if uri is in queue:
#     nothing to do, status should already be set to pending
# if uri is not in db:
#     create document with empty version and status pending
#     enqueue in indexing queue
# if uri in db but without indexed version: has never been indexed
#     update document with status pending
#     enqueue in indexing queue
# if uri in db and with indexed_version but version changed or is unkown: content may have changed
#     update document with status pending
#     enqueue in indexing queue
# if uri in db and indxed_version is the same:
#     nothing to do
