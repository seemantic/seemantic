# seemantic

## Installation

You will need:
* nvm
* uv (with python 3.12)

## Principles

* Self-hostabled: using either APIs or local llms / embeddings / parsing
* Simple: it shouldn't be harder to setup than a docker-compose or harder to use than a consumer app like a search engine, a cloud drive, or a chatbot.
* Enterprise-ready: it should be scalable and follow zero-trust principles (authentication, encryption, RBAC...)
* Pragmatic: the goal is to deliver the expected result, no AI-magic or purity.

## MVP Specifications

* Can be self-hosted o barebone server without GPU with a docker-compose command
* Ask a question, get an answer with references
* add / remove files
* Ability to update without loosing data
* Integration tests to ensure reliability
* Works for pdf, md, docx (only text)


## Tech stack

Each componant with the following objectives in mind:
* Open-source
* Compatible with both self-hosting and cloud
* Scalable
* Multi-tenant compatible
* Standard
* Cost-efficient
* Without vendor lock-in

### Storage
* Documents storage: S3-compatible (self-hosted MinIO by default).
* Application Database: Postgres.
* vector database: lanceDB.
* Conversation history: Postgres?


### backend
* Web server: FastAPI.
* Indexing: Python worker
* Authentication: Zitadel
* Right management: ?
* Encryption: ?

### frontend
* Purely local (compatible with CDN)
* Vite
* Tanstack router
* React
* Dexie

## Security:

* Each tier (or subspace) has a symmetric key
* Each user has a asymmetric key derived from their password
* For each user, we store the symmetric key encrypted with their public asymetric key
* When a user make a request, he send a derived version of its password (after being authenticated, see ZKP, PAKE), this derivate key is used to get the assymetric private key to decrypt the symmetric key
* This symmetric key is never stored, so no-one can access the data (even platform owner)
* See Shamir’s Secret Sharing (SSS) for recovery
