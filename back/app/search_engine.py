from collections.abc import Callable
from datetime import datetime

from pydantic import BaseModel

# Possibilité: on met tout dans la DB
# accepter un décalage entre les raw sources et la DB

# on veut ingérer le parsing avant le chunking, donc il faut garder les anciennes versions
# dans la db

# si on garde le parsed_hash, on peut updater le reste. parsed_hash est la primare key


# solution alternative:
# dans lance: uniquement parsed_hash -> parsed_content
# dans postgres: doc_uri (primary key) -> parsed_hash, raw_doc_hash


# in postgres: (doc_uri, crawling_datetime) -> (parsed_hash, raw_doc_hash)
# in lance pasedDocRepo: parsed_hash -> parsed_content
# in lance vector: vector -> (parsed_hash, min, max)


class ParsedDocument(BaseModel):
    raw_doc_hash: str
    parsed_doc_hash: str
    doc_uri: str
    crawling_datetime: datetime
    parsed_doc_content: str


# -> nothing unique here
# at regular interval


class SearchDocument(BaseModel):
    raw_doc_hash: str
    parsed_doc_hash: str
    doc_uri: str
    parsed_doc_content: str


class Passage(BaseModel):
    start_index_in_parsed_doc: int
    end_index_in_parsed_doc: int


class SearchResult(BaseModel):
    document: SearchDocument
    passages: list[Passage]


# 1-1 image of crawling
class DocumentSnippet(BaseModel):
    doc_uri: str
    parsed_doc_hash: str
    raw_doc_hash: str
    crawling_datetime: datetime


# clean is based on parsed_doc_hash not being used
# not being used means that


class SearchEngine:

    parsed_doc_hash_to_content: dict[str, str]
    db_ref: list[DocumentSnippet]
    query_to_passage_and_parsed_hash: Callable[[str], list[tuple[int, int, str]]]

    def search(self, query: str) -> list[SearchResult]:
        # 1. embed query

        raise NotImplementedError
