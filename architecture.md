# Software Architecture

## Services Architecture

Architecture goals:

- Easy to self-host (on a CPU server using docker-compose)
- Horizontally scalable (both in compute and storage)
- Support blue-green Deployment (zero downtime)
- Extensible with authentication, encryption, RBAC and multi-tenancy
- Extensible to other document sources
- Extensible to other vector stores

```mermaid
flowchart TD

        External["__External process__ or Browser (through Web Server)"]

        Browser["__Browser__
        Displays sources and documents
        Sends requests and receives references and streamed answers
        Store conversations history with indexedDB
        - *SPA, served by CDN, React, Vite, Tanstack Router*"]


        subgraph Compute["Compute"]
            WebServer["__Web Server__
            Manages user requests
            - *FastApi, stateless, async, horizontally scalable*"]

            Indexer["__Indexer__
            Indexes sources (parsing, chunking, embedding, storage)
            - *Python, background workflow*
            "]
        end

        subgraph Storage["Storage"]
            SourceMinIO["Documents storage
            - *Source of truth, MinIO*"]

            VectorStore["__Vector Store__
            Stores embeddings and parsed documents
            - *LanceDB stored in MinIO, reproducible*"]

            SqlDb["__SQL DB__
            App data, Indexed Documents Metadata
            - *PostgreSQL*"]
        end

        External ---> |1 Uploads docs| SourceMinIO
        Indexer --> |2 Subscribes to docs updates| SourceMinIO
        Indexer --> |3 Stores docs metadata| SqlDb
        Indexer --> |3 Stores indexed docs| VectorStore
        Browser --> |subscribes to docs updates *with SSE*
        Send user requests *with SSE*| WebServer
        WebServer --> |Listen to docs update| SqlDb
        WebServer --> |Retrieve relevent docs to query| VectorStore
```



## Indexing Process

Indexing process goals:

- Resynchronize with the source on cold start or after a process stop
- Minimize expensive operations
- Notify users in real time
- Ensure state remains consistent in case of an error during the indexing process

```mermaid
flowchart TD

        UpdateStatusLegend["User notification"]
        style UpdateStatusLegend stroke:green,stroke-width:2px

        CostlyOp["Expensive operation"]
        style CostlyOp stroke:red,stroke-width:2px

        Startup(["Indexer started"]) --> ComputeDiff["Compute diffs Source <> DB"]
        ComputeDiff --> NotifType
        Notif(["Doc update Notif"])
        Notif --> NotifType{"Upsert or Delete?"}
        NotifType --> |upsert| EnqueueOrNothing{"URI in queue?"}
        NotifType --> |delete| Delete["Delete from Document (cascade Indexed document)"]
        style Delete stroke:green,stroke-width:2px
        EnqueueOrNothing --> |Yes| DoNothing["Do nothing"]
        EnqueueOrNothing --> |No| UriInDb?{"URI in DB?"}
        UriInDb? --> |Yes| SourceVersionChange?{"Doc version changed?"}
        UriInDb? --> |No| UpsertInDb["Upsert doc in DB (pending)"]
        UpsertInDb --> EnqueueUri@{ shape: das, label: "Enqueue URI for indexing" }
        style UpsertInDb stroke:green,stroke-width:2px
        SourceVersionChange? --> |No| DoNothing2["Do nothing"]
        SourceVersionChange? --> |yes| UpsertInDb
        EnqueueUri --> UpdateDocStatusIndexing["Update doc status in DB (indexing)"]
        style UpdateDocStatusIndexing stroke:green,stroke-width:2px
        UpdateDocStatusIndexing --> DownloadDocument["Download and hash raw doc"]
        style DownloadDocument stroke:red,stroke-width:2px
        DownloadDocument --> HashExists?{"Hash in DB?"}
        HashExists? --> |Yes|UpdateDocStatusCompleted["Update doc and status (completed)"]
        HashExists? --> |No|ParseDocument["Parse doc and hash parsed doc"]
        style ParseDocument stroke:red,stroke-width:2px
        ParseDocument --> ParsedDocHashExists?{"parsed doc hash in Vector Store?"}
        ParsedDocHashExists? --> |Yes|UpdateDocStatusCompleted
        ParsedDocHashExists? --> |No|IndexDoc["Index (chunk, embed) and store in vector Store"]
        style IndexDoc stroke:red,stroke-width:2px
        IndexDoc --> UpdateDocStatusCompleted
        style UpdateDocStatusCompleted stroke:green,stroke-width:2px
```

### How is zero-downtime upgrade managed ?

The key of an indexed document in db and vector store is a pair (uri,indexer-version). Therefore several indexer versions can run concurrently. Once the indexing for a new version is completed, the frontend can switch to the new version.

### how indexing failures are managed ?

We use eventual consistency from the point from the point of view od the internal system, but it's strongly consistent from the user point of view:

* SQL db act as source of truth
* Vector store upserts are idempotent

__On upsert__:
1. We check in the sql db if indexing is required
1. We update the vector store
2. We update the db

__On delete__:
1. We delete from the db
2. We delete from the vector store

This ensures that when a document is marked as successfully indexed in the SQL database, it is always present in the vector store.

__On retrieval__:
1. We select from the vector store
2. We only keep documents present in the sql databse

This ensures that "hanging" documents (not yet deleted or not completly inserted) in the vector store do not impact the actual result.