-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics
-- index name pattern: <prefix>_<table_name>_<column_name>_<index_type>


CREATE TYPE document_status AS ENUM ('pending', 'indexing', 'indexing_success', 'indexing_error');

CREATE TABLE seemantic_schema.document(
   id UUID PRIMARY KEY,
   uri TEXT NOT NULL UNIQUE,

   indexed_source_version TEXT, -- info that can be retreived from source without loading content (last update timestamp, hash, version id...)
   indexed_version_raw_hash CHAR(32), -- source independant hash of the raw content
   indexed_version_parsed_hash CHAR(32), -- hash of the parsed content
   last_indexing TIMESTAMPTZ, -- set on last_indexed_version_raw_hash change

   status document_status NOT NULL,
   last_status_change TIMESTAMPTZ NOT NULL,
   error_status_message TEXT, -- set when status is Error

   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE INDEX idx_document_uri ON seemantic_schema.document (uri);
CREATE INDEX idx_document_indexed_version_parsed_hash ON seemantic_schema.document (indexed_version_parsed_hash);

ALTER TABLE seemantic_schema.document 
ADD CONSTRAINT check_error_status_message 
CHECK (status <> 'indexing_error' OR error_status_message IS NOT NULL);


ALTER TABLE seemantic_schema.document
ADD CONSTRAINT check_indexed_fields_consistency
CHECK (
    (indexed_source_version IS NOT NULL AND indexed_version_raw_hash IS NOT NULL AND indexed_version_parsed_hash IS NOT NULL AND last_indexing IS NOT NULL)
    OR (indexed_source_version IS NULL AND indexed_version_raw_hash IS NULL AND indexed_version_parsed_hash IS NULL AND last_indexing IS NULL)