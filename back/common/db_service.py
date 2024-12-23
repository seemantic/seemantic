from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import TIMESTAMP, ForeignKey, MetaData, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, joinedload
from typing import Tuple

class DbSettings(BaseModel, frozen=True):
    username: str
    password: str
    host: str
    port: int
    database: str


Base = declarative_base(metadata=MetaData(schema="seemantic_schema"))


class TableSourceDocument(Base):
    __tablename__ = "source_document"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_uri: Mapped[str] = mapped_column(nullable=False, unique=True)
    current_version_id: Mapped[UUID] = mapped_column(ForeignKey("source_document_version.id"), nullable=False)
    current_indexed_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("source_document_version.id"),
        nullable=True,
    )


class TableRawDocument(Base):
    __tablename__ = "raw_document"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    raw_content_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    current_indexed_document_id: Mapped[UUID | None] = mapped_column(ForeignKey("indexed_document.id"), nullable=True)


class TableSourceDocumentVersion(Base):
    __tablename__ = "source_document_version"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_document_id: Mapped[UUID] = mapped_column(ForeignKey("source_document.id"), nullable=False)
    raw_document_id: Mapped[UUID] = mapped_column(ForeignKey("raw_document.id"), nullable=False)
    last_crawling_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)



class TableIndexedDocument(Base):
    __tablename__ = "indexed_document"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    raw_document_id: Mapped[UUID] = mapped_column(ForeignKey("raw_document.id"), nullable=False)
    indexing_status: Mapped[str] = mapped_column(
        nullable=False,
    )  # Could also use Enum(IndexingStatusEnum) for stricter validation
    parsed_content_hash: Mapped[str | None] = mapped_column()


class SourceDocument(BaseModel):
    id: UUID
    source_uri: str
    current_version_id: UUID
    current_indexed_version_id: UUID | None


class RawDocument(BaseModel):
    id: UUID
    raw_content_hash: str
    current_indexed_document_id: UUID | None


class SourceDocumentVersion(BaseModel):
    id: UUID
    source_document_id: UUID
    raw_document_id: UUID
    last_crawling_datetime: datetime


class IndexedDocument(BaseModel):
    id: UUID
    raw_document_id: UUID
    indexing_status: str
    parsed_content_hash: str | None


def to_source(table_obj: TableSourceDocument) -> SourceDocument:
    return SourceDocument(
        id=table_obj.id,
        source_uri=table_obj.source_uri,
        current_version_id=table_obj.current_version_id,
        current_indexed_version_id=table_obj.current_indexed_version_id
    )


def to_raw(table_obj: TableRawDocument) -> RawDocument:
    return RawDocument(
        id=table_obj.id,
        raw_content_hash=table_obj.raw_content_hash,
        current_indexed_document_id=table_obj.current_indexed_document_id
    )


def to_version(table_obj: TableSourceDocumentVersion) -> SourceDocumentVersion:
    return SourceDocumentVersion(
        id=table_obj.id,
        source_document_id=table_obj.source_document_id,
        raw_document_id=table_obj.raw_document_id,
        last_crawling_datetime=table_obj.last_crawling_datetime
    )


def to_indexed(table_obj: TableIndexedDocument) -> IndexedDocument:
    return IndexedDocument(
        id=table_obj.id,
        raw_document_id=table_obj.raw_document_id,
        indexing_status=table_obj.indexing_status,
        parsed_content_hash=table_obj.parsed_content_hash
    )

class DbService:

    def __init__(self, settings: DbSettings) -> None:
        url = f"postgresql+asyncpg://{settings.username}:{settings.password}@{settings.host}:{settings.port}/{settings.database}"
        engine = create_async_engine(url, echo=True)
        self.session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async def get_source_documents_from_parsed_hashes(
        self,
        parsed_content_hashes: list[str],
    ) -> list[Tuple[SourceDocument, SourceDocumentVersion, RawDocument, IndexedDocument]]:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(
                TableSourceDocument,
                TableSourceDocumentVersion,
                TableRawDocument,
                TableIndexedDocument
                )
                .join(TableSourceDocumentVersion, TableSourceDocument.current_indexed_version_id == TableSourceDocumentVersion.id)
                .join(TableRawDocument, TableSourceDocumentVersion.raw_document_id == TableRawDocument.id)
                .join(TableIndexedDocument, TableRawDocument.current_indexed_document_id == TableIndexedDocument.id)
                .where(TableIndexedDocument.parsed_content_hash.in_(parsed_content_hashes))
            )

            db_tuples = result.all()
            plain_objs = [
                (to_source(doc[0]),
                 to_version(doc[1]),
                 to_raw(doc[2]),
                 to_indexed(doc[3]))
                for doc in db_tuples]

            return plain_objs


    async def upsert_source_document(
        self,
        uri: str,
        raw_content_hash: str,
        last_crawling_datetime: datetime,
    ) -> UUID:
        """create source_document if it doesn't exist, raw_document if it doesn't exist, and source_document_version if it doesn't exist.
        if source_document_version exists, update source_document_version.last_crawling_datetime. Set source_document.current_version_id to source_document_version.id
        return source_document, raw_document, and source_document_version
        """
        version_id = uuid4()
        async with self.session_factory() as session, session.begin():
            # Check if the source_document exists
            source_document = await session.execute(select(TableSourceDocument).where(TableSourceDocument.source_uri == uri))
            source_document = source_document.scalar()
            if not source_document:
                # Create new SourceDocument
                source_document = TableSourceDocument(
                    id=uuid4(),  # Assuming UUID is generated
                    source_uri=uri,
                    current_version_id=version_id,
                    current_indexed_version_id=None,
                )
                session.add(source_document)

            # Check if the raw_document exists
            raw_document = await session.execute(
                select(TableRawDocument).where(TableRawDocument.raw_content_hash == raw_content_hash),
            )
            raw_document = raw_document.scalar()

            if not raw_document:
                # Create new RawDocument
                raw_document = TableRawDocument(
                    id=uuid4(),  # Assuming UUID is generated
                    raw_content_hash=raw_content_hash,
                    current_indexed_document_id=None,
                )
                session.add(raw_document)

            # Check if the source_document_version exists
            source_document_version = await session.execute(
                select(TableSourceDocumentVersion).where(
                    TableSourceDocumentVersion.source_document_id == source_document.id,
                    TableSourceDocumentVersion.raw_document_id == raw_document.id,
                ),
            )
            source_document_version = source_document_version.scalar()

            if not source_document_version:
                # Create new SourceDocumentVersion
                source_document_version = TableSourceDocumentVersion(
                    id=version_id,  # Assuming UUID is generated
                    source_document_id=source_document.id,
                    raw_document_id=raw_document.id,
                    last_crawling_datetime=last_crawling_datetime,
                )
                session.add(source_document_version)
            else:
                # Update last_crawling_datetime if SourceDocumentVersion exists
                source_document_version.last_crawling_datetime = last_crawling_datetime

            # Update the current_version_id of the SourceDocument
            source_document.current_version_id = source_document_version.id

            raw_id = raw_document.id
            await session.commit()
            return raw_id


    async def create_indexed_document(self, raw_document_id: UUID, parsed_content_hash: str) -> IndexedDocument:
        indexed_document_id = uuid4()
        async with self.session_factory() as session, session.begin():
            indexed_document = TableIndexedDocument(id=indexed_document_id, raw_document_id=raw_document_id, parsed_content_hash=parsed_content_hash, indexing_status="success")
            session.add(indexed_document)

            # Update the current_indexed_document_id of the RawDocument
            raw_document = await session.execute(select(TableRawDocument).where(TableRawDocument.id == raw_document_id))
            raw_document = raw_document.scalar_one()
            raw_document.current_indexed_document_id = indexed_document_id

            # Update the current_indexed_version_id of the SourceDocument
            source_docs = await session.execute(
                select(TableSourceDocument)
                .join(TableSourceDocumentVersion, TableSourceDocument.current_version_id == TableSourceDocumentVersion.id)
                .where(TableSourceDocumentVersion.raw_document_id == raw_document_id)
            )
            source_docs = source_docs.scalars()
            for source_doc in source_docs:
                source_doc.current_indexed_version_id = source_doc.current_version_id

            indexed = to_indexed(indexed_document)
            await session.commit()
            return indexed


