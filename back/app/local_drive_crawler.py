import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from watchfiles import awatch # type: ignore
from app.settings import get_settings
from app.index_document import index_document

@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_task = asyncio.create_task(monitor_directory())
    try:
        yield  # Exception occurs, but we still hit finally
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


async def monitor_directory():
    """
    Monitors the directory for changes and performs an action.
    """
    settings = get_settings()
    async for changes in awatch(settings.seemantic_drive_root):
        for change_type, file_path in changes:
            if change_type == 1:  # File created
                print(f"File created: {file_path}")
                index_document(file_path)
            elif change_type == 2:  # File modified
                print(f"File modified: {file_path}")
            elif change_type == 3:  # File deleted
                print(f"File deleted: {file_path}")

