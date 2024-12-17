import asyncio

from indexer.settings import get_settings
from indexer.indexer import Indexer

settings = get_settings()
indexer = Indexer(settings)

asyncio.run(indexer.start())
