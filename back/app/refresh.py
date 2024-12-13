# the system should match the status of the source at a given time
# we should be able to retrieve:
#      the original uri (even if do not exists anymore)
#      the parsed content at the time of crawling
# we should parse / embbed / index only when necessary
# if DB containes a parsed_hash, it should always exists in parsed_doc_repo and in search_engine
# we shouln't hold more than on doc content in memory at a time

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
from typing import Iterator
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

class DbRawDocument(BaseModel):
    raw_hash: Hash # key
    parsed_hash: Hash # foreign key to parsed document in ParsedDocRepo

class ParsedDocument(BaseModel):
    content: str

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

    def add_if_missing(self, parsed_doc: ParsedDocument) -> Hash:
        raise NotImplementedError()
    
    def remove_if_present(self, parsed_hash: Hash) -> None:
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

    def add_or_replace(self, doc: VectorizedDocument) -> None:
        """based on doc.parsed_doc_hash key"""
        raise NotImplementedError()
    
    def remove_doc(self, parsed_hash: Hash) -> None:
        raise NotImplementedError()


class DbUpdate(BaseModel):
    add: list[DbSourceDocument] = Field(default_factory=list)
    remove: list[DbSourceDocument] = Field(default_factory=list)
    update: list[DbSourceDocument] = Field(default_factory=list) # based on uri key
    new_raw_to_parsed: dict[Hash, Hash] = Field(default_factory=dict)
    # raw to parse to remove are

class Db:

    def update(self, update: DbUpdate) -> None:
        raise NotImplementedError()

    def get_source_if_exists(self, uri: str) -> DbSourceDocument | None:
        raise NotImplementedError()

    def get_raw_if_exists(self, raw_hash: Hash) -> DbRawDocument | None:
        raise NotImplementedError()
    

class SourceRefresher:

    parser: Parser
    parsed_doc_repo: ParsedDocRepo
    vector_store: VectorStore
    vectorizer: Vectorizer
    db: Db


    def _reindex(self, doc: CrawledDocument) -> Hash:
        parsed_doc = self.parser.parse(doc)
        vectorized = self.vectorizer.vectorize(parsed_doc)
        parsed_hash = self.parsed_doc_repo.add_if_missing(parsed_doc)
        self.vector_store.add_or_replace(vectorized)
        return parsed_hash


    def refresh_source(self, source: Source, force_reindex: bool):
        
        crawled_doc: CrawledDocument
        update: DbUpdate = DbUpdate()
        for crawled_doc in source.crawl():
            raw_hash: Hash = hash_source(crawled_doc)
            # 1. manage reindex
            db_raw_doc = self.db.get_raw_if_exists(raw_hash)
            if force_reindex or not db_raw_doc:
                parsed_hash = self._reindex(crawled_doc)
                update.new_raw_to_parsed[raw_hash] = parsed_hash
            # 2. manage db update
            db_source_doc = self.db.get_source_if_exists(crawled_doc.uri)
            if not db_source_doc:
                update.add.append(DbSourceDocument(uri=crawled_doc.uri, raw_hash=raw_hash))
            elif db_source_doc.raw_hash != raw_hash:
                update.update.append(DbSourceDocument(uri=crawled_doc.uri, raw_hash=raw_hash))
        # TODO here: manage delete in db
        self.db.update(update)
        # TODO here: manage delete in vector store and parsed_doc_repo


