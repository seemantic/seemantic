-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics


CREATE TABLE seemantic_schema.raw_document_entry(
   raw_content_hash CHAR(32) PRIMARY KEY,
   parsed_content_hash CHAR(32) NOT NULL,
   last_parsing_datetime TIMESTAMPTZ NOT NULL,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE seemantic_schema.source_document_entry(
   source_uri TEXT PRIMARY KEY,
   raw_content_hash CHAR(32) NOT NULL,
   last_content_update_datetime TIMESTAMPTZ NOT NULL,
   last_crawling_datetime TIMESTAMPTZ NOT NULL,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
   FOREIGN KEY (raw_content_hash) REFERENCES seemantic_schema.raw_document(raw_content_hash)
);



