# the system should match the status of the source at a given time
# we should be able to retrieve:
#      the original uri (even if do not exists anymore)
#      the parsed content at the time of crawling
# we should parse / embbed / index only when necessary
# if DB containes a parsed_hash, it should always exists in parsed_doc_repo and in search_engine
# we shouln't hold more than on doc content in memory at a time
# Move from sources (like MinIO) could appear as two seperate events: add + delete, nad sources might not treat add and update differently.
# At the end we only have 2 events from sources: upsert (update, add, move) and delete, this should not create re_indexing


# 1. crawling a source return a list of (uri)
# 2. for each uri in crawling result:
#       - get raw content
#       - compute raw_content_hash
#       if raw_content_hash not in db (or force_reparse):
#           - parse content
#           - compute parsed_content_hash
#           - if parsed_content_hash missing from parsed_doc_repo, add
#           - if parsed_content_hash missing from vector_store, or "force_reindex":
#               -chunk / embed, then replace content with same parsed_content_hash (delete/add transaction).
#       - keep track of db update to do (uri, raw_content_hash, parsed_content_hash)
# 3. update db (remove / add / update) to match crawling results
# ...at this point, crawling state is matched with DB
# ...if we have several open connections (read on other server) eventual consistency
# ...in vector store might some new parsed hash are not yet taken into account by vector store
# ...we need to to a "checkout_latest". we can keep in DB a "last update_time"
# ...as it's not yet cleaned, search results will point to parsed_hash not in Db anymore
# ...we can just ignore them, as new ones are already added in VS
# 4. remove vector store chunks pointing to parsed_hash not in DB anymore
# 5. remove parsed_hash to content not in Db anymore
# 6. compact / index vs for performance


# => if it fails at any point, we can restart and search results are always valid


from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterator, Literal
from pydantic import BaseModel, Field
from io import BytesIO
import xxhash



class CrawledDocument(BaseModel):
    uri: str
    content: BytesIO

class Source(ABC):
    
    @abstractmethod
    def crawl(self) -> Iterator[CrawledDocument]: ...

class Hash(BaseModel):
    hash: str

class DbSourceDocument(BaseModel):
    uri: str # key
    raw_hash: Hash # foreign key to DbRawDocument (None if cannot be parsed ?)
    last_crawled_at: datetime
    last_updated_at: datetime

class DbRawDocument(BaseModel):
    raw_hash: Hash # key
    parsed_hash: Hash # foreign key to parsed document in ParsedDocRepo
    last_crawled_at: datetime
    last_updated_at: datetime

class ParsedDocument(BaseModel):
    content: str
    parsed_date: datetime

class MinIoSource(Source):
    pass


def hash_source(doc: CrawledDocument) -> Hash:
    doc.content.seek(0)
    bytes_content = doc.content.read()
    hash = xxhash.xxh3_128_hexdigest(bytes_content)
    return Hash(hash=hash)

def hash_parsed(doc: ParsedDocument) -> Hash:
    hash = xxhash.xxh3_128_hexdigest(doc.content)
    return Hash(hash=hash)


class ParsedDocRepo:

    def upsert(self, parsed_doc: ParsedDocument) -> Hash:
        raise NotImplementedError()
    
    def remove_if_present(self, parsed_hash: Hash) -> None:
        raise NotImplementedError()
    
    def get(self, parsed_hash: Hash) -> ParsedDocument | None:
        raise NotImplementedError()

class Parser:

    def parse(self, source_doc: CrawledDocument) -> ParsedDocument:
        raise NotImplementedError()

class Vector(BaseModel):
    pass

class VectorizedChunk(BaseModel):
    min_index: int
    max_index: int
    vector: Vector

class VectorizedDocument(BaseModel):
    parsed_doc_hash: Hash
    parsed_doc: ParsedDocument
    chunks: list[VectorizedChunk]

class Vectorizer:
    def vectorize(self, doc: ParsedDocument) -> VectorizedDocument:
        raise NotImplementedError()

class VectorStore:

    def upsert(self, doc: VectorizedDocument) -> None:
        """based on doc.parsed_doc_hash key"""
        raise NotImplementedError()
    
    def remove_doc(self, parsed_hash: Hash) -> None:
        raise NotImplementedError()

class DbSourceDocumentUpsert(BaseModel):
    uri: str
    raw_hash: Hash


class Db:

    def upsert(self, uri: str, raw_hash: Hash) -> None:
        # insert or update, change last_raw_change_at id raw_hash changed.
        # always update last_crawled_at
        raise NotImplementedError()
    
    def delete(self, uri: str) -> None:
        raise NotImplementedError()

    def get_source_if_exists(self, uri: str) -> DbSourceDocument | None:
        raise NotImplementedError()

    def get_raw_if_exists(self, raw_hash: Hash) -> DbRawDocument | None:
        raise NotImplementedError()
    
    def upsert_raw_to_parsed(self, raw_hash: Hash, parsed_hash: Hash) -> None:
        raise NotImplementedError()

    def get_uris(self) -> list[str]:
        raise NotImplementedError()
    

class SourceRefresher:

    parser: Parser
    parsed_doc_repo: ParsedDocRepo
    vector_store: VectorStore
    vectorizer: Vectorizer
    db: Db

    def _reindex_if_needed(self, raw_hash: Hash, doc: CrawledDocument, force_reindex: bool) -> None:
        if force_reindex or not self.db.get_raw_if_exists(raw_hash):
            self._reindex(raw_hash, doc)

    def _reindex(self, raw_hash: Hash, doc: CrawledDocument) -> None:
        parsed_doc = self.parser.parse(doc)
        vectorized = self.vectorizer.vectorize(parsed_doc)
        parsed_hash = self.parsed_doc_repo.upsert(parsed_doc)
        self.vector_store.upsert(vectorized)
        self.db.upsert_raw_to_parsed(raw_hash, parsed_hash)

    def clean_vector_store(self) -> None:
        """remove vector store chunks pointing to parsed_hash not in DB anymore.
        We delete old enough chunks:
        - in case of concurrent refresh (pre-added chunks before commit)
        """
        raise NotImplementedError()
    
    def clean_parsed_doc_repo(self) -> None:
        """remove parsed_hash not in DB anymore
        as for clean_vector_store we do not remove recently added docs
        """
        raise NotImplementedError()

    def clean_raw_doc_table(self) -> None:
        """remove lines where raw_hash not in source doc DB anymore
        we do not remove recently crawled docs
        - to be resilient to possible issue with crawling
        - to be resilent to move that appears as two seperate events: add + delete
        """
        raise NotImplementedError()

    def clean_index(self)-> None:
        self.clean_raw_doc_table()
        self.clean_vector_store()
        self.clean_parsed_doc_repo()


    def refresh_source(self, source: Source, force_reindex: bool):
        crawled_doc: CrawledDocument
        for crawled_doc in source.crawl():
            self.on_crawl(crawled_doc, force_reindex=force_reindex)
        self.clean_index()


    def on_crawl(self, crawled_doc: CrawledDocument, force_reindex: bool = False) -> None:
        raw_hash: Hash = hash_source(crawled_doc)
        self._reindex_if_needed(raw_hash=raw_hash, doc=crawled_doc, force_reindex=force_reindex)
        self.db.upsert(uri=crawled_doc.uri, raw_hash=raw_hash)

    
    def on_delete(self, uri: str):
        self.db.delete(uri)