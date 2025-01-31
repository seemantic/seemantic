-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics
-- index name pattern: <prefix>_<table_name>_<column_name>_<index_type>


CREATE TYPE document_status AS ENUM ('pending', 'indexing', 'indexing_success', 'indexing_error');

CREATE TABLE seemantic_schema.document(
   id UUID PRIMARY KEY,
   uri TEXT NOT NULL UNIQUE,

   source_specific_current_version_id TEXT, -- source specific version identifier that can be used to track changes from sources without having to fetch the whole document. it could be a content hash or a version id.
   current_version_raw_hash CHAR(32),
   last_modification TIMESTAMPTZ, -- set on current_version_raw_hash change

   last_indexed_version_raw_hash CHAR(32),
   last_indexing TIMESTAMPTZ, -- set on last_indexed_version_raw_hash change

   status document_status NOT NULL,
   last_status_change TIMESTAMPTZ NOT NULL,
   error_status_message TEXT, -- set when status is Error

   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE INDEX idx_document_uri ON seemantic_schema.document (uri);
CREATE INDEX idx_document_last_indexed_version_raw_hash ON seemantic_schema.document (last_indexed_version_raw_hash);

ALTER TABLE seemantic_schema.document 
ADD CONSTRAINT check_error_status_message 
CHECK (status <> 'indexing_error' OR error_status_message IS NOT NULL);