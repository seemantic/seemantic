from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ApiIndexedContentHash(BaseModel):
    parsed_hash: str
    raw_hash: str


class ApiDocumentSnippet(BaseModel):
    uri: str  # relative path within source
    status: Literal["pending", "indexing", "indexing_success", "indexing_error"]
    error_status_message: str | None
    last_indexing: datetime | None
    indexed_content_hash: ApiIndexedContentHash | None


class ApiParsedDocument(BaseModel):
    hash: str
    markdown_content: str


class ApiDocumentDelete(BaseModel):
    uri: str


class ApiExplorer(BaseModel):
    documents: list[ApiDocumentSnippet]


class ApiSearchResultChunk(BaseModel):
    content: str
    start_index_in_doc: int
    end_index_in_doc: int


class ApiSearchResult(BaseModel):
    document_uri: str
    chunks: list[ApiSearchResultChunk]


class ApiChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ApiQueryResponseUpdate(BaseModel):
    # if not None, it's the continuation of the answer
    # if None, keep the previous answer.
    delta_answer: str | None
    # if None, keep the previous result.
    # if not None, it replace the previous search result
    search_results: list[ApiSearchResult] | None
    # if None, keep the previous chat messages
    # if not None, it replace the previous chat messages
    chat_messages_exchanged: list[ApiChatMessage] | None


class ApiQueryResponseMessage(BaseModel):
    answer: str
    search_result: list[ApiSearchResult]
    chat_messages_exchanged: list[ApiChatMessage]


class ApiQueryMessage(BaseModel):
    content: str


class ApiQueryReponsePair(BaseModel):
    query: ApiQueryMessage
    response: ApiQueryResponseMessage


class ApiQuery(BaseModel):
    query: ApiQueryMessage
    previous_messages: list[ApiQueryReponsePair]


ApiEventType = Literal["update", "delete"]
