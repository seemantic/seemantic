import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from watchfiles import Change, awatch  # type: ignore[reportUnknownVariable]

from app.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):  # noqa: ANN201
    monitor_task = asyncio.create_task(monitor_directory())
    try:
        yield  # Exception occurs, but we still hit finally
    finally:
        monitor_task.cancel()
        with suppress(asyncio.CancelledError):
            await monitor_task


async def monitor_directory() -> None:
    """Monitors the directory for changes and performs an action."""
    settings = get_settings()
    async for changes in awatch(settings.seemantic_drive_root):
        for change_type, _ in changes:  # _: path
            if change_type in (Change.added, Change.modified, Change.deleted):  # File modified
                pass
