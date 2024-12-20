-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics
-- index name pattern: <prefix>_<table_name>_<column_name>_<index_type>



CREATE TABLE seemantic_schema.indexed_document_entry(
   raw_content_hash CHAR(32) PRIMARY KEY,
   last_indexing_status TEXT NOT NULL,
   last_start_indexing_datetime TIMESTAMPTZ NOT NULL,
   last_successful_indexing_parsed_content_hash CHAR(32),
   last_successful_indexing_datetime TIMESTAMPTZ,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE seemantic_schema.source_document_entry(
   source_uri TEXT PRIMARY KEY,

   last_indexing_raw_content_hash CHAR(32), -- set before indexing
   last_successful_indexing_raw_content_hash CHAR(32), -- set after successful indexing

   last_crawling_datetime TIMESTAMPTZ NOT NULL, -- updated when we check if content has changed
   last_start_indexing_datetime TIMESTAMPTZ, -- updated when last_indexing_raw_content_hash changes
   last_sucessful_indexing_datetime TIMESTAMPTZ, -- updated when last_successful_indexing_raw_content_hash changes
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

   FOREIGN KEY (last_indexing_raw_content_hash) REFERENCES seemantic_schema.indexed_document_entry(raw_content_hash),
   FOREIGN KEY (last_successful_indexing_raw_content_hash) REFERENCES seemantic_schema.indexed_document_entry(raw_content_hash)
);

/* 
A: new document
1) a document is crawled, it's hash is computed
2) if no indexed_document_entry exists with this hash, we create it with last_indexing_status == "pending"
3) source_document_entry is created or updated with last_indexing_raw_content_hash, and eventually last_successful_indexing_raw_content_hash
4) we start indexing, once indexing is finished (failed or success),
   - we update or create indexed_document_entry
   - we update source_document_entry having this last_crawling_raw_content_hash with last_successful_indexing_raw_content_hash
B: new crawling
when the document is crawled again:
   - if content did not change, we update last_crawling_datetime
   - if content changed, we go back to 1
C: force reindex
when we reindex, it's always an existing indexed_document_entry, go back to 3

On file explorer:
- we display all source_document_entry. either pending / indexed / failed depending on the linked last_indexing_raw_content_hash
- we can display sucess if last_successful_indexing_raw_content_hash is not null

On search:
- we find chunk in vectorized, we find related last_parsed_content_hash in indexed_document_entry
- we join on source_document_entry last_successful_indexing_raw_content_hash
 */