# MVP TODO LIST

- Can host the app on a server (no login)
- A Docker-compose to run everything
- Requires a Mistral API Key in config
- Can add / remove / move rename files and directories
- Can do a one-turn request and get a streamed request
- Can open files + passage from reference or file tree
- manage pdf, md, txt, word files
- manage only text

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

# DOING

- [Bug] When a new file is added in MinIO, it does not appears in UI (need refresh or even restart)

# DONE

- [Bug] on refresh, the conv message is restreamed instead of loaded from db
- [QA] Fix linters
- [Bug] app crash when user click on nested link
- [Feat] Implement File-Tree
