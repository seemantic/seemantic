import asyncio

from indexer.indexer import Indexer
from indexer.settings import get_settings

settings = get_settings()
indexer = Indexer(settings)

asyncio.run(indexer.start())
