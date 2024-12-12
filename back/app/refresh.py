def refresh() -> None:
    """crawls sources and refreshes db and search engine.
    only semantic drive source is supported for now"""
    update_db()  #  first step to update Documents explore
    update_parsed_docs()
    update_search_engine()


class DocumentId:
    source: str
    uri: str  # generic location identifier
    xxh3_128: str


def get_index() -> list[DocumentId]:
    raise NotImplementedError


def update_db() -> None:
    raise NotImplementedError


def update_parsed_docs() -> None:
    raise NotImplementedError


def update_search_engine() -> None:
    raise NotImplementedError
