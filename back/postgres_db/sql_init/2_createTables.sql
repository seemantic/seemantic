-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics
-- index name pattern: <prefix>_<table_name>_<column_name>_<index_type>

CREATE TYPE document_status AS ENUM ('pending', 'indexing', 'indexing_success', 'indexing_error');


CREATE TABLE seemantic_schema.indexed_content(
   id UUID PRIMARY KEY,
   raw_hash CHAR(32) NOT NULL, -- source independant hash of the raw content
   parsed_hash CHAR(32) NOT NULL, -- hash of the parsed content
   indexer_version SMALLINT NOT NULL,

   UNIQUE (raw_hash, indexer_version)
);


CREATE TABLE seemantic_schema.document(
   id UUID PRIMARY KEY,
   uri TEXT NOT NULL UNIQUE,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE seemantic_schema.indexed_document(
   id UUID PRIMARY KEY,
   document_id UUID REFERENCES seemantic_schema.document(id) ON DELETE CASCADE NOT NULL,
   uri TEXT NOT NULL,
   indexer_version SMALLINT NOT NULL,
   indexed_source_version TEXT, -- info that can be retreived from source without loading content (last update timestamp, hash, version id...)
   indexed_content_id UUID REFERENCES seemantic_schema.indexed_content(id), -- set when status is indexing_success
   last_indexing TIMESTAMPTZ, -- set when indexed_content_id is updated
   status document_status NOT NULL,
   last_status_change TIMESTAMPTZ NOT NULL,
   error_status_message TEXT, -- set when status is Error
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

   UNIQUE (document_id, indexer_version)
);


CREATE INDEX idx_document_uri ON seemantic_schema.document (uri);
CREATE INDEX idx_indexed_document_indexed_content_id ON seemantic_schema.indexed_document (indexed_content_id);
CREATE INDEX idx_indexed_content_parsed_hash ON seemantic_schema.indexed_content (parsed_hash);

ALTER TABLE seemantic_schema.indexed_document
ADD CONSTRAINT check_error_status_message 
CHECK (status <> 'indexing_error' OR error_status_message IS NOT NULL);

-- check that indexed_source_version, indexed_content_id and last_indexing are either all null or all not null
ALTER TABLE seemantic_schema.indexed_document
ADD CONSTRAINT check_indexed_content_id
CHECK (
   (indexed_source_version IS NULL AND indexed_content_id IS NULL AND last_indexing IS NULL) OR
   (indexed_source_version IS NOT NULL AND indexed_content_id IS NOT NULL AND last_indexing IS NOT NULL)
);


CREATE OR REPLACE FUNCTION update_indexed_document_uri()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the uri in indexed_document when the uri in document changes
    UPDATE seemantic_schema.indexed_document
    SET uri = NEW.uri
    WHERE document_id = NEW.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_indexed_document_uri
AFTER INSERT OR UPDATE OF uri ON seemantic_schema.document
FOR EACH ROW
EXECUTE FUNCTION update_indexed_document_uri();


-- Notify table changes

CREATE OR REPLACE FUNCTION notify_table_changes()
RETURNS TRIGGER AS $$
DECLARE
   operation TEXT;
   row_data JSON;
   table_name TEXT;
BEGIN
   table_name := TG_TABLE_NAME;
   operation := TG_OP;
   IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
      row_data := to_json(NEW);
   ELSIF TG_OP = 'DELETE' THEN
      row_data := to_json(OLD);
   END IF;
   PERFORM pg_notify('table_changes', json_build_object('table', table_name, 'operation', operation, 'data', row_data)::TEXT);
   RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER indexed_document_changes_trigger
AFTER INSERT OR UPDATE OR DELETE ON seemantic_schema.indexed_document
FOR EACH ROW EXECUTE FUNCTION notify_table_changes();