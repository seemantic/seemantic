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
raw_hash: hash available when loaded.
status: just to display in db
is_indexed: set once it's set into vector store, to keep file green even as status changes (waiting, loading)
last_version_is_indexed: when last set raw_hash is in VS (indexing up to date) set to false when raw_hash changed (loaded) but indexing is not finished yet (or failed) 
last_modification (raw_hash change)
status (status change)
error_status_message: set when last_status_update is Error.

## in vector store
vector -> raw_hash + chunk, indexing_algo_version
raw_hash-> file_content_parsed, indexing_algo_version

## use cases
* file deleted: remove in DB. at regular interval, clean VS from raw_hash not in db anymore
* file renamed: (add+remove): perform add / remove, indexing will be instantenous because of raw_hash in VS
* file added: add, then index, the update
* file content changed, update then index, then update
* indexing algo changed (parsing, embedding, indexing): only a VS process -> add vectors / files with a new algo version.
* indexing service started: recrawl all urls.
* client ask global status: Download DB
* client makes a query: query VS for a given algo, load files in DB with this raw_hash, return source docs from DB and parsed docs from VS.
-> HOW TO RETRIEVES FILES THAT HAS BEEN MODIFIED BUT NOT YET REINDEXED ?
* client click a file: load file from uri in source, load parsed from VS, might not be consistent, we don't care.
