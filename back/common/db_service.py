from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import MetaData, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

DATABASE_URL = "postgresql+asyncpg://seemantic_back:seemantic_back_test_pwd@localhost:5432/postgres"


DbBase = declarative_base(metadata=MetaData(schema="seemantic_schema"))


class DbSourceDocumentEntry(DbBase):
    __tablename__ = "source_document_entry"

    uri: Mapped[str] = mapped_column(primary_key=True)
    raw_content_hash: Mapped[str]
    last_crawling_datetime: Mapped[datetime]
    last_content_update_datetime: Mapped[datetime]


class DbRawDocumentEntry(DbBase):
    __tablename__ = "raw_document_entry"

    raw_content_hash: Mapped[str] = mapped_column(primary_key=True)
    parsed_content_hash: Mapped[str]
    last_parsing_datetime: Mapped[datetime]


class ResourceConflictError(Exception):
    """Raised when a unique constraint is violated."""


class SourceDocumentEntry(BaseModel):
    uri: str
    raw_content_hash: str
    last_crawling_datetime: datetime
    last_content_update_datetime: datetime


class RawDocumentEntry(BaseModel):
    raw_content_hash: str
    parsed_content_hash: str
    last_parsing_datetime: datetime


class DbService:

    def __init__(self) -> None:
        pass

    engine = create_async_engine(DATABASE_URL, echo=True)

    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async def update_crawling_datetime(self, uri: str, crawling_datetime: datetime) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(
                update(DbSourceDocumentEntry)
                .where(DbSourceDocumentEntry.uri == uri)
                .values(last_crawling_datetime=crawling_datetime),
            )
            await session.commit()

    async def upsert_source_document(self, source_document: SourceDocumentEntry) -> None:
        async with self.session_factory() as session, session.begin():
            db_doc = DbSourceDocumentEntry(
                uri=source_document.uri,
                raw_content_hash=source_document.raw_content_hash,
                last_crawling_datetime=source_document.last_crawling_datetime,
                last_content_update_datetime=source_document.last_content_update_datetime,
            )
            await session.merge(db_doc)
            await session.commit()

    async def upsert_raw_document(self, raw_document: RawDocumentEntry) -> None:
        async with self.session_factory() as session, session.begin():
            db_doc = DbRawDocumentEntry(
                raw_content_hash=raw_document.raw_content_hash,
                parsed_content_hash=raw_document.parsed_content_hash,
                last_parsing_datetime=raw_document.last_parsing_datetime,
            )
            await session.merge(db_doc)
            await session.commit()

    async def select_all_source_documents(self) -> list[SourceDocumentEntry]:
        async with self.session_factory() as session, session.begin():
            db_docs = await session.execute(select(DbSourceDocumentEntry))
            return [
                SourceDocumentEntry(
                    uri=db_doc.uri,
                    raw_content_hash=db_doc.raw_content_hash,
                    last_crawling_datetime=db_doc.last_crawling_datetime,
                    last_content_update_datetime=db_doc.last_content_update_datetime,
                )
                for db_doc in db_docs.scalars()
            ]

    async def get_raw_if_exists(self, raw_content_hash: str) -> RawDocumentEntry | None:
        async with self.session_factory() as session, session.begin():
            db_doc = await session.execute(
                select(DbRawDocumentEntry).where(DbRawDocumentEntry.raw_content_hash == raw_content_hash),
            )
            return db_doc.scalar()

    async def delete_source_documents(self, uris: list[str]) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(delete(DbSourceDocumentEntry).where(DbSourceDocumentEntry.uri.in_(uris)))
            await session.commit()
