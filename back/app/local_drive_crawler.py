import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from watchfiles import awatch  # type: ignore

from app.index_document import index_document
from app.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    monitor_task = asyncio.create_task(monitor_directory())
    try:
        yield  # Exception occurs, but we still hit finally
    finally:
        monitor_task.cancel()
        with suppress(asyncio.CancelledError):
            await monitor_task


async def monitor_directory():
    """Monitors the directory for changes and performs an action."""
    settings = get_settings()
    async for changes in awatch(settings.seemantic_drive_root):
        for change_type, file_path in changes:
            if change_type == 1:  # File created
                index_document(file_path)
            elif change_type == 2 or change_type == 3:  # File modified
                pass
