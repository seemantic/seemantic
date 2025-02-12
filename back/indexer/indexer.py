import asyncio
import datetime as dt
import logging
from datetime import datetime
from typing import cast

from pydantic import BaseModel

from common.db_service import DbDocument, DbDocumentIndexedVersion, DbService, TableDocumentStatusEnum
from common.document import ParsableFileType, is_parsable
from common.embedding_service import EmbeddingService
from common.utils import hash_file_content
from common.vector_db import VectorDB
from indexer.chunker import Chunker
from indexer.parser import Parser
from indexer.settings import Settings
from indexer.source import Source, SourceDeleteEvent, SourceDocumentReference, SourceUpsertEvent
from indexer.sources.seemantic_drive import SeemanticDriveSource


class RawDocIndexationResult(BaseModel):
    raw_content_hash: str


class IndexingError(Exception):
    public_error: str
    internal_error: Exception | None

    def __init__(self, public_error: str, internal_error: Exception | None = None) -> None:
        super().__init__(public_error)
        self.public_error = public_error
        self.internal_error = internal_error

    def __str__(self) -> str:
        if self.internal_error:
            return f"{self.public_error} (Internal error: {self.internal_error})"
        return self.public_error


class Indexer:

    source: Source
    db: DbService
    parser: Parser = Parser()
    chunker: Chunker = Chunker()
    embedder: EmbeddingService
    vector_db: VectorDB
    uris_queue: asyncio.Queue[str]
    uris_in_queue: set[str]
    queue_started: asyncio.Event
    background_task_process_queue: asyncio.Task[None]  # so it's not garbage collected, cf. RUF006

    def __init__(self, settings: Settings) -> None:
        self.embedder = EmbeddingService(token=settings.jina_token)
        self.vector_db = VectorDB(settings.minio, self.embedder.distance_metric())
        self.source = SeemanticDriveSource(settings=settings.minio)
        self.db = DbService(settings.db)
        self.uris_queue = asyncio.Queue(maxsize=10000)
        self.uris_in_queue = set()
        self.queue_started = asyncio.Event()

    async def _init(self) -> None:
        await self.vector_db.connect()
        self.background_task_process_queue = asyncio.create_task(self.process_queue())

    async def _set_indexing_error(self, uri: str, public_error: str, internal_error: Exception | None = None) -> None:
        logging.warning(f"indexing error for document {uri}: {internal_error or public_error}")
        await self.db.update_documents_status([uri], TableDocumentStatusEnum.indexing_error, public_error)

    async def process_queue(self) -> None:
        self.queue_started.set()
        logging.info("Indexing queue started")
        while True:
            uri = await self.uris_queue.get()
            try:
                self.uris_in_queue.remove(uri)  # uri can be re-added to queue as soon as processing starts
                logging.info(f"Start indexing: {uri}")
                await self.index_and_store(uri)
            except IndexingError as e:
                logging.exception(f"Error indexing {uri}")
                await self._set_indexing_error(uri, e.public_error)
            except Exception:
                logging.exception(f"Unexpected error indexing {uri}")
                await self._set_indexing_error(uri, "Unknown error")
            self.uris_queue.task_done()

    async def index_and_store(self, uri: str) -> None:

        # Update document status to indexing
        await self.db.update_documents_status([uri], TableDocumentStatusEnum.indexing, None)

        # Retrieve the source document
        source_doc = await self.source.get_document(uri)
        if source_doc is None:
            raise IndexingError(public_error="Document not found in source")

        # Check if the file type is parsable
        if not is_parsable(source_doc.filetype):
            raise IndexingError(public_error=f"Unsupported file type {source_doc.filetype}")

        # check if raw hash changed
        raw_hash = hash_file_content(source_doc.content)
        db_doc = await self.db.get_document(uri)
        if db_doc.indexed_version is not None and db_doc.indexed_version.raw_hash == raw_hash:
            logging.info(f"raw_hash did not change for {uri}, indexing skipped")
            await self.db.update_documents_status([uri], TableDocumentStatusEnum.indexing_success, None)
        else:
            logging.info(f"Parsing {uri}")
            filetype = cast(ParsableFileType, source_doc.filetype)
            parsed = self.parser.parse(filetype, source_doc.content)
            if await self.vector_db.is_indexed(parsed):
                logging.info(f"parsed_hash already indexed, indexing skipped for {uri}")
                await self.db.update_documents_status([uri], TableDocumentStatusEnum.indexing_success, None)
            else:
                logging.info(f"Chunking {uri}")
                chunks = self.chunker.chunk(parsed)
                logging.info(f"Embedding {uri}")
                embedded_chunks = await self.embedder.embed_document(parsed, chunks)
                logging.info(f"Storing {uri}")
                parsed_hash = await self.vector_db.index(parsed, embedded_chunks)
                logging.info(f"Indexing completed for {uri}")

                # Update the indexed version in the database
                await self.db.update_documents_indexed_version(
                    uri,
                    DbDocumentIndexedVersion(
                        raw_hash=raw_hash,
                        parsed_hash=parsed_hash,
                        source_version=source_doc.doc_ref.source_version_id,
                        last_modification=datetime.now(tz=dt.timezone.utc),
                    ),
                )

    async def enqueue_doc_refs(self, refs: list[SourceDocumentReference]) -> None:
        for ref in refs:
            self.uris_in_queue.add(
                ref.uri,
            )  # when uri is added to queue, unique set should already be updated (so it can be removed)
            self.uris_queue.put_nowait(ref.uri)

    async def manage_upserts(self, refs: list[SourceDocumentReference], uri_to_db_docs: dict[str, DbDocument]) -> None:
        docs_to_index: list[SourceDocumentReference] = []
        docs_to_create: list[SourceDocumentReference] = []
        for doc_ref in refs:
            uri = doc_ref.uri
            if uri in self.uris_in_queue:
                continue
            db_doc = uri_to_db_docs.get(uri)
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

        if docs_to_create:
            await self.db.create_documents([doc.uri for doc in docs_to_create])
        if docs_to_index:
            await self.db.update_documents_status(
                [doc.uri for doc in docs_to_index],
                TableDocumentStatusEnum.pending,
                None,
            )
        if docs_to_index or docs_to_create:
            docs_enqueued = docs_to_index + docs_to_create
            logging.info(f"Enqueuing documents: {docs_enqueued}")
            await self.enqueue_doc_refs(docs_enqueued)

    async def start(self) -> None:
        logging.info("Starting indexer")
        await self._init()
        await self.queue_started.wait()  # we should not enqueue before queue is listening

        source_doc_refs = await self.source.all_doc_refs()
        uri_to_doc_refs = {doc_ref.uri: doc_ref for doc_ref in source_doc_refs}
        db_docs = await self.db.get_all_documents()
        uri_to_db = {doc.uri: doc for doc in db_docs}

        await self.manage_upserts(source_doc_refs, uri_to_db)
        to_delete = set(uri_to_db.keys()) - set(uri_to_doc_refs.keys())
        if to_delete:
            await self.db.delete_documents(list(to_delete))

        async for event in self.source.listen():
            if isinstance(event, SourceUpsertEvent):
                uri_to_db = await self.db.get_documents([event.doc_ref.uri])
                await self.manage_upserts([event.doc_ref], uri_to_db)
            else:
                assert isinstance(event, SourceDeleteEvent)
                await self.db.delete_documents([event.uri])

        logging.info("Indexer stopped")


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
