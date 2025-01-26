-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics
-- index name pattern: <prefix>_<table_name>_<column_name>_<index_type>


CREATE TABLE seemantic_schema.source_document(
   id UUID PRIMARY KEY,
   source_uri TEXT NOT NULL UNIQUE,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
   current_version_id UUID,
   current_indexed_version_id UUID,
   last_indexing_process_status TEXT NOT NULL,
   last_indexing_error_message TEXT
);

CREATE TABLE seemantic_schema.raw_document(
   id UUID PRIMARY KEY,
   raw_content_hash CHAR(32) NOT NULL UNIQUE,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
   current_indexed_document_id UUID
);

CREATE TABLE seemantic_schema.source_document_version(
   id UUID PRIMARY KEY,
   source_document_id UUID NOT NULL,
   raw_document_id UUID NOT NULL,
   FOREIGN KEY (source_document_id) REFERENCES seemantic_schema.source_document(id) ON DELETE CASCADE,
   FOREIGN KEY (raw_document_id) REFERENCES seemantic_schema.raw_document(id),
   UNIQUE (source_document_id, raw_document_id),
   last_crawling_datetime TIMESTAMPTZ NOT NULL,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE seemantic_schema.indexed_document(
   id UUID PRIMARY KEY,
   raw_document_id UUID NOT NULL,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
   parsed_content_hash CHAR(32) NOT NULL,
   FOREIGN KEY (raw_document_id) REFERENCES seemantic_schema.raw_document(id) ON DELETE CASCADE
);

ALTER TABLE seemantic_schema.raw_document
ADD CONSTRAINT fk_seemantic_schema_raw_document_current_indexed_document_id
FOREIGN KEY (current_indexed_document_id)
REFERENCES seemantic_schema.indexed_document(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE seemantic_schema.source_document
ADD CONSTRAINT fk_seemantic_schema_source_document_current_version_id
FOREIGN KEY (current_version_id)
REFERENCES seemantic_schema.source_document_version(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE seemantic_schema.source_document
ADD CONSTRAINT fk_seemantic_schema_source_document_current_indexed_version_id
FOREIGN KEY (current_indexed_version_id)
REFERENCES seemantic_schema.source_document_version(id) DEFERRABLE INITIALLY DEFERRED;


/*
A) crawling:
A.a) source update: create source / raw and source_version
1) a document (uri/hash) is crawled. In a transaction:
    - if uri does not exists, we create a source_document
    - if raw_document with this raw_content_hash does not exists, we create it
    - we check if a source_document_version exists with same uri same hash
      - if yes, last_crawling_datetime is updated
      - if no, we create a new source_document_version

A.b) indexing. input: raw_document
1) we do the actual indexing
2) if it's OK we update the version with "success"/parsing_hash, else "error"

B) file explorer: source_document + status
1) select all source_document, join with last source_document_version + raw_document + last indexed_document

C) click on document
C.a) open source
C.b) open parsed: from source_document_version for a given source_document, find the latest sucessful indexed_document

C) search
indexed_document -> raw_document -> source_document_version -> source_document. exclude those with a more recent version with an indexed version
NB: can be done by clean during indexing.

D) delete
simple delete
*/

