# MVP TODO LIST

## Functional

- manage pdf, md, txt, word files
- searchable only through text
- Can add / remove / move / rename files and directories (directly using tree)
- can display doc (by clicking tree) as markdown if it has been indexed (click on tree or on ref). Not clickable if file is not indexed
- agent RAG, multi-turn conversation, reset by user

## Technical

- Can host the app on a server (no login)
- A Docker-compose to run everything
- Requires an liteLLM-compatible config

## TODO

- [QA] Check ESLint config
- [CI] run linters in CI
- [Feat] Implemnt file view
- [QA] test conversation in rest api test
- [QA] add unit tests, improve test coverage
- [DEP] Add plug-and-play Docker-compose
- [DOC] add proper readme doc for users
- [UI] make it pretty
- [Feat] add authent
- [Bug] If user changes litellm embedding settings, it should change the indexer version
- [Bug] display grow as the answer is written when a doc is not displayed (no splitter)
- [Feat] add / delete / rename files and folders in file tree
- [Bug] files not (yet)successfully indexed are clickable but it raise an error as there is not parsed version -> icon indexed/indexing/error in the tree.
- [CI] Replace scripts by proper setup (use https://taskfile.dev/installation/)

# DOING

- [Bug] seemantic_drive bucket is not created at startup.

# DONE

- [Bug] error on delete (and not taken into account)
- [Bug] on refresh, the conv message is restreamed instead of loaded from db
- [QA] Fix linters
- [Bug] app crash when user click on nested link
- [Feat] Implement File-Tree
- [Bug] When a new file is added in MinIO, it does not appears in UI (need refresh or even restart)
