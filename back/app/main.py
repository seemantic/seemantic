import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.db_service import ResourceConflictError
from app.local_drive_crawler import lifespan
from app.rest_api import router

app = FastAPI(lifespan=lifespan)


@app.exception_handler(ResourceConflictError)
async def resource_conflict_handler(request: Request, exception: ResourceConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exception)},
    )


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)  # type: ignore
