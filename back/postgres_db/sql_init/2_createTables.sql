-- All tables has
-- id: primary_key
-- creation_datetime, last_modification_datetime: for diagnostics


CREATE TABLE seemantic_schema.document(
   id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
   creation_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
   last_modification_datetime TIMESTAMPTZ NOT NULL,
   url TEXT NOT NULL, -- if source is seemantic drive, it's the seemantic drive url (not the original file url).
   title TEXT NOT NULL,
   sha_256 CHAR(64) NOT NULL -- sha256
);
