import asyncio
import logging
from indexer.indexer import Indexer
from indexer.settings import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

settings = get_settings()
indexer = Indexer(settings)

asyncio.run(indexer.start())
