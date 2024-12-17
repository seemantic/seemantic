from common.db_service import DbService
from indexer.settings import Settings
from indexer.source import DeleteEvent, Source, UpsertEvent
from indexer.sources.seemantic_drive import SeemanticDriveSource
from xxhash import xxh3_128_hexdigest
from io import BytesIO

def hash_file_content(content: BytesIO) -> str:
    content.seek(0)
    bytes_content = content.read()
    raw_hash = xxh3_128_hexdigest(bytes_content)
    return raw_hash


class Indexer:

    source: Source
    db: DbService


    def __init__(self, settings: Settings) -> None:
        self.source = SeemanticDriveSource(settings=settings.minio)


    async def _reindex_if_needed(self, uri: str) -> None:
        pass

    async def _on_delete(self, uri: str) -> None:
        pass

    async def start(self) -> None:


        uris_in_source = await self.source.all_uris()

        for uri in uris_in_source:
            await self._reindex_if_needed(uri)

        # Delete missing documents
        uris_in_db = await self.db.select_all_source_documents()
        deleted_uris = set(uri.uri for uri in uris_in_db) - set(uris_in_source)
        await self.db.delete_source_documents(list(deleted_uris))

        async for doc_event in self.source.listen():
            if isinstance(doc_event, DeleteEvent):
                await self._on_delete(doc_event.uri)
            else:
                assert isinstance(doc_event, UpsertEvent)
                print(hash_file_content(doc_event.content))
                await self._reindex_if_needed(doc_event.uri)
