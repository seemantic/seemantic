import uvicorn
from fastapi import FastAPI

from app.rest_api import router, lifespan

app = FastAPI(lifespan=lifespan)


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)  # type: ignore[ReportUnknownMember]
