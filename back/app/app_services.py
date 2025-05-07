from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.generator import Generator
from app.search_engine import SearchEngine
from app.settings import DepSettings
from common.db_service import DbService
from common.embedding_service import EmbeddingService
from common.minio_service import MinioService
from common.vector_db import VectorDB


@lru_cache
def get_minio_service(settings: DepSettings) -> MinioService:
    return MinioService(settings=settings.minio)


DepMinioService = Annotated[MinioService, Depends(get_minio_service)]


@lru_cache
def get_db_service(settings: DepSettings) -> DbService:
    return DbService(settings=settings.db)


DepDbService = Annotated[DbService, Depends(get_db_service)]


@lru_cache
def get_search_engine(settings: DepSettings, db: DepDbService) -> SearchEngine:
    embedding_service = EmbeddingService(token=settings.jina_token)
    return SearchEngine(
        embedding_service=embedding_service,
        vector_db=VectorDB(settings.lance_db, embedding_service.distance_metric(), settings.indexer_version),
        db=db,
        indexer_version=settings.indexer_version,
    )


DepSearchEngine = Annotated[SearchEngine, Depends(get_search_engine)]


@lru_cache
def get_generator_service(settings: DepSettings) -> Generator:
    return Generator(settings.generator, settings.generator__litellm_api_key)


DepGenerator = Annotated[Generator, Depends(get_generator_service)]
