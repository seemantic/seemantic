import asyncio
import logging
from typing import cast
from uuid import UUID

from pydantic import BaseModel

from common.db_service import DbDocument, DbIndexedContent, DbService, TableIndexedDocumentStatusEnum
from common.document import ParsableFileType, is_parsable
from common.embedding_service import EmbeddingService
from common.utils import hash_file_content
from common.vector_db import VectorDB
from indexer.chunker import Chunker
from indexer.parser import Parser
from indexer.settings import Settings
from indexer.source import Source, SourceDeleteEvent, SourceDocumentReference, SourceUpsertEvent
from indexer.sources.seemantic_drive import SeemanticDriveSource

logging = logging.getLogger(__name__)


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


class DocToIndex(BaseModel, frozen=True):
    source_ref: SourceDocumentReference
    indexed_doc_id: UUID


class Indexer:
    source: Source
    db: DbService
    parser: Parser = Parser()
    chunker: Chunker = Chunker()
    embedder: EmbeddingService
    vector_db: VectorDB
    docs_to_index_queue: asyncio.Queue[DocToIndex]
    uris_in_queue: set[
        str
    ]  # to not re-add uri to queue if already in it (cap queue size to the number of documents in source)
    queue_started: asyncio.Event  # to signal that the queue is started
    background_task_process_queue: asyncio.Task[
        None
    ]  # keep a ref to the queue processing task, so it's not garbage collected, cf. RUF006

    def __init__(self, settings: Settings) -> None:
        self.embedder = EmbeddingService(settings.embedding, settings.embedding__litellm_api_key)
        self.vector_db = VectorDB(settings.lance_db, self.embedder.distance_metric(), settings.indexer_version)
        self.source = SeemanticDriveSource(settings=settings.minio)
        self.db = DbService(settings.db)
        self.docs_to_index_queue = asyncio.Queue(maxsize=10000)
        self.uris_in_queue = set()
        self.queue_started = asyncio.Event()
        self.indexer_version = settings.indexer_version

    async def _start_queue_processing(self) -> None:
        """Start the queue processing task, return only when the processing actually started"""
        self.background_task_process_queue = asyncio.create_task(self._process_queue())
        await self.queue_started.wait()

    async def _set_indexing_error(
        self,
        indexed_doc_id: UUID,
        public_error: str,
        internal_error: Exception | None = None,
    ) -> None:
        """set the document status to indexing error in case of error during indexing (parsing, embedding...)"""
        logging.warning(f"indexing error for document {indexed_doc_id}: {internal_error or public_error}")
        await self.db.update_indexed_documents_status(
            [indexed_doc_id],
            TableIndexedDocumentStatusEnum.indexing_error,
            public_error,
        )

    async def _process_queue(self) -> None:
        """Infinite loop waiting for updated documents to index"""
        self.queue_started.set()
        logging.info("Indexing queue started")
        while True:
            doc_to_index = await self.docs_to_index_queue.get()
            uri = doc_to_index.source_ref.uri
            indexed_doc_id = doc_to_index.indexed_doc_id
            try:
                self.uris_in_queue.remove(uri)  # uri can be re-added to queue as soon as processing starts
                logging.info(f"Start indexing: {uri}")
                await self._index_and_store(doc_to_index)
            except IndexingError as e:
                logging.exception(f"Error indexing {uri}")
                await self._set_indexing_error(indexed_doc_id, e.public_error)
            except Exception:
                logging.exception(f"Unexpected error indexing {uri}")
                await self._set_indexing_error(indexed_doc_id, "Unknown error")
            self.docs_to_index_queue.task_done()

    async def _index_and_store(self, doc_to_index: DocToIndex) -> None:
        """indexing workflow for one enqeued document"""
        # Update document status to indexing
        indexed_doc_id = doc_to_index.indexed_doc_id
        uri = doc_to_index.source_ref.uri
        await self.db.update_indexed_documents_status([indexed_doc_id], TableIndexedDocumentStatusEnum.indexing, None)

        # Retrieve the source document
        source_doc = await self.source.get_document(uri)
        if source_doc is None:
            raise IndexingError(public_error="Document not found in source")

        # Check if the file type is parsable
        if not is_parsable(source_doc.filetype):
            raise IndexingError(public_error=f"Unsupported file type {source_doc.filetype}")

        # check if raw hash changed
        raw_hash = hash_file_content(source_doc.content)
        indexed_content = await self.db.get_indexed_content_if_exists(raw_hash, self.indexer_version)
        if indexed_content:
            # raw hash already indexed, no need to parse again
            indexed_content_id = indexed_content[0]
            logging.info(
                f"content with raw_hash {raw_hash} already indexed for {uri} with id {indexed_content_id}, indexing skipped",
            )
        else:
            # raw hash not found in indexed documents
            logging.info(f"Parsing {uri}")
            filetype = cast("ParsableFileType", source_doc.filetype)
            parsed = self.parser.parse(uri, filetype, source_doc.content)
            if await self.vector_db.is_indexed(parsed.hash):
                logging.info(f"parsed_hash already indexed, indexing skipped for {uri}")
            else:
                logging.info(f"Chunking {uri}")
                chunks = self.chunker.chunk(parsed)
                logging.info(f"Embedding {uri}")
                embedded_chunks = await self.embedder.embed_document(parsed, chunks)
                logging.info(f"Storing {uri} in vector db")
                await self.vector_db.index(parsed, embedded_chunks)
                logging.info(f"Mark content as indexed in db for {uri}")

            # upsert indexed content
            indexed_content_id = await self.db.upsert_indexed_content(
                DbIndexedContent(raw_hash=raw_hash, parsed_hash=parsed.hash),
                self.indexer_version,
            )

        # update document indexed content id
        logging.info(f"Mark document as indexed in db for {uri}")
        await self.db.update_indexed_document_indexed_content_id(
            indexed_doc_id,
            source_doc.doc_ref.source_version_id,
            indexed_content_id,
        )
        logging.info(f"indexing process completed for {uri}")

    async def _enqueue_doc_refs(self, refs: list[DocToIndex]) -> None:
        for ref in refs:
            self.uris_in_queue.add(
                ref.source_ref.uri,
            )  # when uri is added to queue, unique set should already be updated (so it can be removed)
            self.docs_to_index_queue.put_nowait(ref)

    async def _manage_upserts(self, refs: list[SourceDocumentReference], uri_to_db_docs: dict[str, DbDocument]) -> None:
        """Qualify documents to be indexed and enqueue them if needed"""
        docs_to_update: list[DocToIndex] = []
        docs_to_create: list[DocToIndex] = []
        new_doc_refs: list[SourceDocumentReference] = []
        for doc_ref in refs:
            uri = doc_ref.uri
            if uri in self.uris_in_queue:
                continue
            db_doc = uri_to_db_docs.get(uri)
            if db_doc is None:
                new_doc_refs.append(doc_ref)
            elif (
                db_doc.last_indexing is None
                or db_doc.indexed_source_version is None
                or doc_ref.source_version_id is None
                or db_doc.indexed_source_version != doc_ref.source_version_id
            ):
                # doc might have changed
                docs_to_update.append(DocToIndex(source_ref=doc_ref, indexed_doc_id=db_doc.indexed_document_id))
            else:
                # doc did not change since last successful indexing
                continue

        if new_doc_refs:
            uri_to_created_indexed_id = await self.db.create_indexed_documents(
                [doc.uri for doc in new_doc_refs],
                self.indexer_version,
            )
            docs_to_create = [
                DocToIndex(source_ref=doc_ref, indexed_doc_id=uri_to_created_indexed_id[doc_ref.uri])
                for doc_ref in new_doc_refs
            ]
        if docs_to_update:
            await self.db.update_indexed_documents_status(
                [doc.indexed_doc_id for doc in docs_to_update],
                TableIndexedDocumentStatusEnum.pending,
                None,
            )
        if docs_to_update or docs_to_create:
            docs_enqueued = docs_to_update + docs_to_create
            logging.info(f"Enqueuing documents: {docs_enqueued}")
            await self._enqueue_doc_refs(docs_enqueued)

    async def start(self) -> None:
        """Start the indexer
        1. Make a list of document diffs between source and db, process the diff
        2. Listen to source events and process them as they come
        """
        logging.info("Starting indexer")
        await self._start_queue_processing()

        source_doc_refs = await self.source.all_doc_refs()
        uri_to_doc_refs = {doc_ref.uri: doc_ref for doc_ref in source_doc_refs}
        db_docs = await self.db.get_all_documents(indexer_version=self.indexer_version)
        uri_to_db = {doc.uri: doc for doc in db_docs}

        await self._manage_upserts(source_doc_refs, uri_to_db)
        to_delete = set(uri_to_db.keys()) - set(uri_to_doc_refs.keys())
        if to_delete:
            await self.db.delete_documents(list(to_delete))

        async for event in self.source.listen():
            if isinstance(event, SourceUpsertEvent):
                uri_to_db = await self.db.get_documents([event.doc_ref.uri], self.indexer_version)
                await self._manage_upserts([event.doc_ref], uri_to_db)
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
