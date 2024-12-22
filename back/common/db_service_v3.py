from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import TIMESTAMP, MetaData, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from datetime import datetime
from uuid import UUID, uuid4
from typing import Tuple


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
    current_version_id: Mapped[UUID] = mapped_column(ForeignKey('source_document_version.id'), nullable=False)
    current_indexed_document_id: Mapped[UUID | None] = mapped_column(ForeignKey('source_document_version.id'), nullable=True)


class RawDocument(Base):
    __tablename__ = 'raw_document'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    raw_content_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    current_indexed_document_id: Mapped[UUID | None] = mapped_column(ForeignKey('indexed_document.id'), nullable=True)


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
    


    async def get_source_documents_by_indexed_document_ids(self, indexed_document_ids: list[UUID]) -> list[SourceDocument]:
        async with self.session_factory() as session, session.begin():
            db_doc = await session.execute(
                select(SourceDocument)
                .join(SourceDocumentVersion, SourceDocument.id == SourceDocumentVersion.source_document_id)
                .join(RawDocument, SourceDocumentVersion.raw_document_id == RawDocument.id)
                .join(IndexedDocument, RawDocument.id == IndexedDocument.raw_document_id)
                .where(IndexedDocument.id.in_(indexed_document_ids))
            )
            return list(db_doc.scalars())
        

    async def upsert_source_document(self, uri: str, raw_content_hash: str, last_crawling_datetime: datetime) -> Tuple[SourceDocument, RawDocument, SourceDocumentVersion]:
        """create source_document if it doesn't exist, raw_document if it doesn't exist, and source_document_version if it doesn't exist.
        if source_document_version exists, update source_document_version.last_crawling_datetime. Set source_document.current_version_id to source_document_version.id
        return source_document, raw_document, and source_document_version
        """ 
        async with self.session_factory() as session, session.begin():
            # Check if the source_document exists
            source_document = await session.execute(
                select(SourceDocument).where(SourceDocument.source_uri == uri)
            )
            source_document = source_document.scalar()

            if not source_document:
                # Create new SourceDocument
                source_document = SourceDocument(
                    id=uuid4(),  # Assuming UUID is generated
                    source_uri=uri,
                    current_version_id=None,
                    current_indexed_document_id=None
                )
                session.add(source_document)

            # Check if the raw_document exists
            raw_document = await session.execute(
                select(RawDocument).where(RawDocument.raw_content_hash == raw_content_hash)
            )
            raw_document = raw_document.scalar()

            if not raw_document:
                # Create new RawDocument
                raw_document = RawDocument(
                    id=uuid4(),  # Assuming UUID is generated
                    raw_content_hash=raw_content_hash,
                    current_indexed_document_id=None
                )
                session.add(raw_document)

            # Check if the source_document_version exists
            source_document_version = await session.execute(
                select(SourceDocumentVersion).where(
                    SourceDocumentVersion.source_document_id == source_document.id,
                    SourceDocumentVersion.raw_document_id == raw_document.id
                )
            )
            source_document_version = source_document_version.scalar()

            if not source_document_version:
                # Create new SourceDocumentVersion
                source_document_version = SourceDocumentVersion(
                    id=uuid4(),  # Assuming UUID is generated
                    source_document_id=source_document.id,
                    raw_document_id=raw_document.id,
                    last_crawling_datetime=last_crawling_datetime
                )
                session.add(source_document_version)
            else:
                # Update last_crawling_datetime if SourceDocumentVersion exists
                source_document_version.last_crawling_datetime = last_crawling_datetime

            # Update the current_version_id of the SourceDocument
            source_document.current_version_id = source_document_version.id

            await session.commit()

            return source_document, raw_document, source_document_version




    async def get_source_documents_impacted_by_raw_document(self, raw_document_id: UUID) -> list[SourceDocument]:
        async with self.session_factory() as session, session.begin():
            db_doc = await session.execute(
                select(SourceDocument)
                .join(SourceDocumentVersion, SourceDocument.last_version_id == SourceDocumentVersion.id)
                .join(RawDocument, SourceDocumentVersion.raw_document_id == RawDocument.id)
                .where(RawDocument.id == raw_document_id)
            )
            return list(db_doc.scalars())
        
