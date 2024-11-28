import uvicorn
from fastapi import FastAPI

from app.local_drive_crawler import lifespan
from app.rest_api import router

app = FastAPI(lifespan=lifespan)


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)  # type: ignore[ReportUnknownMember]
