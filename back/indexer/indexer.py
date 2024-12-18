import logging

from common.db_service import DbService, RawDocumentEntry, SourceDocumentEntry
from indexer.settings import Settings
from indexer.source import Source, SourceDeleteEvent, SourceUpsertEvent
from indexer.sources.seemantic_drive import SeemanticDriveSource


class Indexer:

    source: Source
    db: DbService

    def __init__(self, settings: Settings) -> None:
        self.source = SeemanticDriveSource(settings=settings.minio)

    async def _reindex_if_needed(self, uri: str) -> None:

        source_doc = await self.source.get_document(uri)
        if not source_doc:
            logging.warning(f"Source document not found: {uri}")
            return
        raw_in_db = await self.db.get_raw_if_exists(source_doc.raw_content_hash)
        if raw_in_db:
            await self.db.update_crawling_datetime(uri, source_doc.crawling_datetime)
        else:
            # 1) parse
            # 2) store parsed
            # 2) vectorize
            # TODO(NICO): change parsed_content_hash and last_parsed_update
            await self.db.upsert_raw_document(
                RawDocumentEntry(
                    raw_content_hash=source_doc.raw_content_hash,
                    parsed_content_hash="TODO",
                    last_parsing_datetime=source_doc.crawling_datetime,
                ),
            )
            await self.db.upsert_source_document(
                source_document=SourceDocumentEntry(
                    uri=uri,
                    raw_content_hash=source_doc.raw_content_hash,
                    last_crawling_datetime=source_doc.crawling_datetime,
                    last_content_update_datetime=source_doc.crawling_datetime,
                ),
            )

    """     def _reindex_if_needed(self, raw_hash: Hash, doc: OriginDocument, *, force_reindex: bool) -> None:
            if force_reindex or not self.db.get_raw_if_exists(raw_hash):
                self._reindex(raw_hash, doc)

        def _reindex(self, raw_hash: Hash, doc: OriginDocument) -> None:
            parsed_doc = self.parser.parse(doc)
            vectorized = self.vectorizer.vectorize(parsed_doc)
            parsed_hash = self.parsed_doc_repo.upsert(parsed_doc)
            self.vector_store.upsert(vectorized)
            self.db.upsert_raw_to_parsed(raw_hash, parsed_hash) """

    async def start(self) -> None:

        uris_in_source = await self.source.all_uris()

        for uri in uris_in_source:
            await self._reindex_if_needed(uri)

        # Delete documents not in source anymore
        uris_in_db = await self.db.select_all_source_documents()
        deleted_uris = {uri.uri for uri in uris_in_db} - set(uris_in_source)
        await self.db.delete_source_documents(list(deleted_uris))

        async for doc_event in self.source.listen():
            if isinstance(doc_event, SourceDeleteEvent):
                await self.db.delete_source_documents([doc_event.uri])
            else:
                assert isinstance(doc_event, SourceUpsertEvent)
                await self._reindex_if_needed(doc_event.uri)
