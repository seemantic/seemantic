from datetime import datetime
from sysconfig import get_scheme_names
from pydantic import BaseModel
from sqlalchemy import TIMESTAMP, MetaData, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from datetime import datetime
from uuid import UUID


DATABASE_URL = "postgresql+asyncpg://seemantic_back:seemantic_back_test_pwd@localhost:5432/postgres"


class DbSettings(BaseModel, frozen=True):
    username: str
    password: str
    host: str
    port: int
    database: str


Base = declarative_base(metadata=MetaData(schema="seemantic_schema"))

class SourceDocument(Base):
    __tablename__ = 'source_document'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_uri: Mapped[str] = mapped_column(nullable=False, unique=True)


class RawDocument(Base):
    __tablename__ = 'raw_document'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    raw_content_hash: Mapped[str] = mapped_column(nullable=False, unique=True)


class SourceDocumentVersion(Base):
    __tablename__ = 'source_document_version'

    id: Mapped[UUID] = mapped_column(Uprimary_key=True)
    source_document_id: Mapped[UUID] = mapped_column(ForeignKey('source_document.id'), nullable=False)
    raw_document_id: Mapped[UUID] = mapped_column(ForeignKey('raw_document.id'), nullable=False)
    last_crawling_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class IndexedDocument(Base):
    __tablename__ = 'indexed_document'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    raw_document_id: Mapped[UUID] = mapped_column(ForeignKey('raw_document.id'), nullable=False)
    creation_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    indexing_status: Mapped[str] = mapped_column(nullable=False)  # Could also use Enum(IndexingStatusEnum) for stricter validation
    parsed_content_hash: Mapped[str | None] = mapped_column()


class DbService:

    def __init__(self, settings: DbSettings) -> None:
        url = f"postgresql+asyncpg://{settings.username}:{settings.password}@{settings.host}:{settings.port}/{settings.database}"
        engine = create_async_engine(url, echo=True)
        self.session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async def get_source_document(self, source_uri: str) -> SourceDocument | None:
        async with self.session_factory() as session, session.begin():
            db_doc = await session.execute(
                select(SourceDocument).where(SourceDocument.source_uri == source_uri),
            )
            return db_doc.scalar() 

    async def create_source_document(self, uri: str) -> None:
        async with self.session_factory() as session:
            source_document = SourceDocument(source_uri=uri)
            session.add(source_document)
            await session.commit()

    async def get_raw_document(self, raw_content_hash: str) -> RawDocument | None:
        async with self.session_factory() as session, session.begin():
            db_doc = await session.execute(
                select(RawDocument).where(RawDocument.raw_content_hash == raw_content_hash),
            )
            return db_doc.scalar()

    async def create_raw_document(self, raw_content_hash: str) -> None:
        async with self.session_factory() as session:
            raw_document = RawDocument(raw_content_hash=raw_content_hash)
            session.add(raw_document)
            await session.commit()

    async def create_source_document_version(self, source_document_id: UUID, raw_document_id: UUID, last_crawling_datetime: datetime) -> None:
        async with self.session_factory() as session:
            source_document_version = SourceDocumentVersion(source_document_id=source_document_id, raw_document_id=raw_document_id, last_crawling_datetime=last_crawling_datetime)
            session.add(source_document_version)
            await session.commit()

    async def get_source_document_version(self, source_document_id: UUID) -> SourceDocumentVersion | None:
        async with self.session_factory() as session, session.begin():
            db_doc = await session.execute(
                select(SourceDocumentVersion).where(SourceDocumentVersion.source_document_id == source_document_id),
            )
            return db_doc.scalar()
        
    async def update_crawling_datetime(self, source_document_id: UUID, raw_document_id: UUID, last_crawling_datetime: datetime) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(
                update(SourceDocumentVersion)
                .where(SourceDocumentVersion.source_document_id == source_document_id)
                .where(SourceDocumentVersion.raw_document_id == raw_document_id)
                .values(last_crawling_datetime=last_crawling_datetime),
            )
            await session.commit()