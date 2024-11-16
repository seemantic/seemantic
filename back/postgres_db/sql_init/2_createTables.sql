-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics


CREATE TABLE seemantic_schema.document(
   id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
   last_modification_datetime TIMESTAMPTZ NOT NULL,
   path TEXT NOT NULL, -- if source is seemantic drive, it's the path relative to the seemantic drive path.
   filename TEXT NOT NULL, -- name of the file when it was uploaded
   sha_256 CHAR(64) NOT NULL -- sha256 of the file content
   UNIQUE (path, filename)
);
