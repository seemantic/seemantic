import asyncio

from indexer.indexer import Indexer

indexer = Indexer()

asyncio.run(indexer.start())
