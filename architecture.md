# Software Architecture

## Services Architecture

Architecture goals:

- Easy to self-host (on a small CPU server with a simple docker-compose)
- Uncoupled from a specific vector store (separated from App DB)
- Scale horizontally (in compute and storage)
- Support Blue-Green Deployment (zero downtime)
- Compatible with authentication, encryption, RBAC and multi-tenancy

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

- Minimize costly operations
- Notify users in real time

```mermaid
flowchart TD
        Notif(["Doc update Notif"])
        Notif --> NotifType{"Upsert or Delete?"}
        NotifType --> |upsert| EnqueueOrNothing{"URI in queue?"}
        NotifType --> |delete| Delete["Delete from Document (cascade Indexed document)"]
        style Delete fill:#99ff99
        EnqueueOrNothing --> |Yes| DoNothing["Do nothing"]
        EnqueueOrNothing --> |No| UriInDb?{"URI in DB?"}
        UriInDb? --> |Yes| SourceVersionChange?{"Doc version changed?"}
        UriInDb? --> |No| UpsertInDb["Upsert doc in DB (pending)"]
        UpsertInDb --> EnqueueUri@{ shape: das, label: "Enqueue URI for indexing" }
        style UpsertInDb fill:#99ff99
        SourceVersionChange? --> |No| DoNothing2["Do nothing"]
        SourceVersionChange? --> |yes| UpsertInDb
        style UpsertInDb fill:#99ff99
        EnqueueUri --> UpdateDocStatusIndexing["Update doc status in DB (indexing)"]
        style UpdateDocStatusIndexing fill:#99ff99
        UpdateDocStatusIndexing --> DownloadDocument["Download and hash raw doc"]
        style DownloadDocument fill:#f9f
        DownloadDocument --> HashExists?{"Hash in DB?"}
        HashExists? --> |Yes|UpdateDocStatusCompleted["Update doc and status (completed)"]
        HashExists? --> |No|ParseDocument["Parse doc and hash parsed doc"]
        style ParseDocument fill:#f9f
        ParseDocument --> ParsedDocHashExists?{"parsed doc hash in Vector Store?"}
        ParsedDocHashExists? --> |Yes|UpdateDocStatusCompleted
        ParsedDocHashExists? --> |No|IndexDoc["Index (chunk, embed) and store in vector Store"]
        style IndexDoc fill:#f9f
        IndexDoc --> UpdateDocStatusCompleted
        style UpdateDocStatusCompleted fill:#99ff99
```