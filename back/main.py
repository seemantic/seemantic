import uvicorn
from fastapi import FastAPI
import logging
from app.rest_api import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)  # type: ignore[ReportUnknownMember]
