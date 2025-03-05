# seemantic

## Principles

* Can be self-hosted, using either APIs or local llms / embeddings
* In Saas mode, data is as secure and private as possible while maintaining practicity

## MVP Specifications

* Can be self-hosted o barebone server without GPU with a docker-compose command
* Ask a question, get an answer with references
* add / remove files
* Ability to update without loosing data
* Integration tests to ensure reliability
* Works for pdf, md, docx (only text)


## Tasks

TODO: add integration tests
TODO: add front
TODO: add prod setup script
TODO: fix lancedb warning ([2025-03-02T15:43:14Z WARN  lance_table::io::commit] Using unsafe commit handler. Concurrent writes may result in data loss. Consider providing a commit handler that prevents conflicting writes.)

## Security:

* Each tier (or subspace) has a symmetric key
* Each user has a asymmetric key derived from their password
* For each user, we store the symmetric key encrypted with their public asymetric key
* When a user make a request, he send a derived version of its password (after being authenticated, see ZKP, PAKE), this derivate key is used to get the assymetric private key to decrypt the symmetric key
* This symmetric key is never stored, so no-one can access the data (even platform owner)
* See Shamir’s Secret Sharing (SSS) for recovery