-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics
-- index name pattern: <prefix>_<table_name>_<column_name>_<index_type>


CREATE TYPE document_status AS ENUM ('pending', 'indexing', 'indexing_success', 'indexing_error');



CREATE TABLE seemantic_schema.indexed_content(
   id UUID PRIMARY KEY,
   raw_hash CHAR(32) NOT NULL UNIQUE, -- source independant hash of the raw content
   parsed_hash CHAR(32) NOT NULL, -- hash of the parsed content
   last_indexing TIMESTAMPTZ NOT NULL, -- set on last_indexed_version_raw_hash change
   indexer_version SMALLINT NOT NULL
);


CREATE TABLE seemantic_schema.document(
   id UUID PRIMARY KEY,
   uri TEXT NOT NULL UNIQUE,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE seemantic_schema.indexed_document(
   id UUID PRIMARY KEY,
   source_document_id UUID REFERENCES seemantic_schema.document(id) ON DELETE CASCADE NOT NULL,
   indexer_version SMALLINT NOT NULL,
   indexed_source_version TEXT, -- info that can be retreived from source without loading content (last update timestamp, hash, version id...)
   indexed_content_id UUID REFERENCES seemantic_schema.indexed_content(id), -- set when status is indexing_success
   status document_status NOT NULL,
   last_status_change TIMESTAMPTZ NOT NULL,
   error_status_message TEXT, -- set when status is Error
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

   UNIQUE (source_document_id, indexer_version)
);


CREATE INDEX idx_document_uri ON seemantic_schema.document (uri);
CREATE INDEX idx_indexed_document_indexed_content_id ON seemantic_schema.indexed_document (indexed_content_id);
CREATE INDEX idx_indexed_content_parsed_hash ON seemantic_schema.indexed_content (parsed_hash);

ALTER TABLE seemantic_schema.indexed_document
ADD CONSTRAINT check_error_status_message 
CHECK (status <> 'indexing_error' OR error_status_message IS NOT NULL);
