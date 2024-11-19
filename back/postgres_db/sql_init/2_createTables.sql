-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics




CREATE TABLE seemantic_schema.document_snippet(
   id uuid PRIMARY KEY,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
   last_modification_datetime TIMESTAMPTZ NOT NULL,
   relative_path TEXT NOT NULL, -- if source is seemantic drive, it's the filepath relative to the seemantic drive path.
   UNIQUE (relative_path)
);
