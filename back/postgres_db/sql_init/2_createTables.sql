-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics
-- index name pattern: <prefix>_<table_name>_<column_name>_<index_type>



CREATE TABLE seemantic_schema.indexed_document_entry(
   raw_content_hash CHAR(32) PRIMARY KEY,
   last_indexing_status TEXT NOT NULL,
   last_indexing_datetime TIMESTAMPTZ NOT NULL,
   last_successful_indexing_parsed_content_hash CHAR(32),
   last_successful_indexing_datetime TIMESTAMPTZ,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE seemantic_schema.source_document_entry(
   source_uri TEXT PRIMARY KEY,

   last_crawling_raw_content_hash CHAR(32) NOT NULL, -- set after crawling changing content
   last_indexing_raw_content_hash CHAR(32), -- set after indexing
   last_successful_indexing_raw_content_hash CHAR(32), -- set after successful indexing

   last_crawling_datetime TIMESTAMPTZ NOT NULL, -- updated when we check if content has changed
   last_content_update_datetime TIMESTAMPTZ NOT NULL, -- updated when last_crawling_raw_content_hash changes
   last_indexing_datetime TIMESTAMPTZ, -- updated when last_indexing_raw_content_hash changes
   last_sucessful_indexing_datetime TIMESTAMPTZ, -- updated when last_successful_indexing_raw_content_hash changes
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

   FOREIGN KEY (last_indexing_raw_content_hash) REFERENCES seemantic_schema.indexed_document_entry(raw_content_hash),
   FOREIGN KEY (last_successful_indexing_raw_content_hash) REFERENCES seemantic_schema.indexed_document_entry(raw_content_hash)
);

/* 
A: new document
1) a document is crawled: source_document_entry is created or updated with last_crawling_raw_content_hash
2) if no indexed_document_entry with raw_content_hash == last_crawling_raw_content_hash andlast_indexing_status == "success" exists, we index it
3) once indexing is finished (failed or success),
   - we update or create indexed_document_entry
   - we update source_document_entry having this last_crawling_raw_content_hash with last_indexing_raw_content_hash and eventually last_successful_indexing_raw_content_hash
B: new crawling
when the document is crawled again:
   - if content did not change, we update last_crawling_datetime
   - if content changed, we go back to 1
C: force reindex
when we reindex, it's always an existing indexed_document_entry, go back to 3
 */


 