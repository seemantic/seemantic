# seemantic


## Data flow

1. crawling detect a document
2. we compute a list of pairs (uri,raw_hash). each file can be:
    1. added (new uri, new hash)
    2. removed (existing uri not found)
    3. renamed (new uri, existing hash, existing uri not found)
    4. modified (existing uri with a different hash)
    5. copy-pasted (new uri, existing hash, existing uri found with same hash)
3. do we have a parsed version for this raw_hash ?



```mermaid
graph TD;
    document_detected-->uri_hash_pair;
    uri_hash_pair-->;
    B-->D;
    C-->D;
```



## reflexion

- fast api app is not built to manage long running process in the backgroun
- if we scale fastAPI on several servers, only one shoud manage index building
- ...we should have a separate process


gerer les fichiers invalides et non parsable ?
pas possible de prévénir à l'ingestion car:
- ne marche que pour seemantic_drive
- on ne peut pas savoir si le parsing va fail


####

## in DB
url
current_version_raw_hash: hash available when loaded.
last_indexed_version_raw_hash: set after it is indexed: we know if last version is indexed by comparing this with 'current_version_raw_hash', this field is to map it from VS. we also know if some version is indexed just if this field is not None.
status: just to display in db
last_modification (raw_hash change, just for display)
status (status change, just for display)
error_status_message: set when last_status_update is Error.

## in vector store
vector -> raw_hash + chunk, indexing_algo_version
raw_hash-> file_content_parsed, indexing_algo_version

## use cases
* file deleted: remove in DB. at regular interval, clean VS from raw_hash not in db anymore
* file renamed: (add+remove): perform add / remove, indexing will be instantenous because of raw_hash in VS
* file added: add, then index, the update
* file content changed, update current_version_raw_hash, then index, then update last_indexed_version_raw_hash
* indexing algo changed (parsing, embedding, indexing): only a VS process -> add vectors / files with a new algo version.
* indexing service started: recrawl all urls.
* client ask global status: Download DB
* client makes a query: query VS for a given algo, load files in DB with this last_indexed_version_raw_hash, return source docs from DB and parsed docs from VS.
* client click a file: load file from uri in source, load parsed from VS using last_indexed_version_raw_hash, might not be consistent, we don't care.
