import pytest

from indexer.indexer import Indexer
from indexer.settings import get_settings


@pytest.fixture(scope="module", autouse=True)
def start_background_processes() -> None:
    # start minio
    # start db
    # start indexer

    settings = get_settings()
    _: Indexer = Indexer(settings)

    # teardown


def test_happy_path() -> None:
    # - start the server
    # - start the indexed
    # 1) upload a new document
    # 2) create a query
    # 3) check the answer
    # 4) update the document
    # 5) ask the query again
    # 6) check the answer is updated
    # 7) delete the document
    # 8) ask the query again
    # 9) check the answer is deleted
    pass


def test_indexer_restart() -> None:
    pass


def test_server_restart() -> None:
    pass


def test_unparsable_file() -> None:
    pass


def test_hug_file() -> None:
    pass
