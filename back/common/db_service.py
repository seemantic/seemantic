import datetime as dt
import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import TIMESTAMP, Enum, ForeignKey, MetaData, delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from uuid_utils import uuid7

from back import indexer



class DbSettings(BaseModel, frozen=True):
    username: str
    password: str
    host: str
    port: int
    database: str


Base = declarative_base(metadata=MetaData(schema="seemantic_schema"))


class TableDocumentStatusEnum(enum.Enum):
    # nb. for some reason, if i put the enum lable in uppercase, it does not work (it passes 'PENDING' to the db)
    pending = "pending"
    indexing = "indexing"
    indexing_success = "indexing_success"
    indexing_error = "indexing_error"


class TableIndexedContent(Base):
    __tablename__ = "indexed_content"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    raw_hash: Mapped[str] = mapped_column(nullable=False)
    parsed_hash: Mapped[str] = mapped_column(nullable=False)
    last_indexing: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class TableDocument(Base):
    __tablename__ = "document"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(nullable=False, unique=True)
    creation_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class TableIndexedDocument(Base):
    __tablename__ = "indexed_document"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("document.id"), nullable=False)

    # version
    indexed_source_version: Mapped[str | None] = mapped_column(nullable=True)
    indexed_content_id: Mapped[UUID | None] = mapped_column(ForeignKey("indexed_content.id"), nullable=True)
    indexer_version: Mapped[int] = mapped_column(nullable=False)

    # status
    status: Mapped[TableDocumentStatusEnum] = mapped_column(
        Enum(TableDocumentStatusEnum, name="document_status"),
        nullable=False,
    )
    last_status_change: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    error_status_message: Mapped[str] = mapped_column(nullable=True)

    creation_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class DbIndexedContent(BaseModel):
    raw_hash: str
    parsed_hash: str
    last_indexing: datetime


class DbDocumentStatus(BaseModel):
    status: TableDocumentStatusEnum
    last_status_change: datetime
    error_status_message: str | None


class DbDocument(BaseModel):
    uri: str
    indexed_source_version: str | None
    indexed_content: DbIndexedContent | None
    status: DbDocumentStatus


def to_doc(row_doc: TableIndexedDocument, row_indexed_content: TableIndexedContent | None) -> DbDocument:

    indexed_content = (
        DbIndexedContent(
            raw_hash=row_indexed_content.raw_hash,
            parsed_hash=row_indexed_content.parsed_hash,
            last_indexing=row_indexed_content.last_indexing,
        )
        if row_indexed_content
        else None
    )

    return DbDocument(
        uri=row_doc.uri,
        indexed_source_version=row_doc.indexed_source_version,
        indexed_content=indexed_content,
        status=DbDocumentStatus(
            status=row_doc.status,
            last_status_change=row_doc.last_status_change,
            error_status_message=row_doc.error_status_message,
        ),
    )


class DbService:

    indexer_version: int

    def __init__(self, settings: DbSettings, indexer_version: int) -> None:
        url = f"postgresql+asyncpg://{settings.username}:{settings.password}@{settings.host}:{settings.port}/{settings.database}"
        engine = create_async_engine(url, echo=True)  # add connect_args={"timeout": 10} in production ?
        self.session_factory = async_sessionmaker(engine, class_=AsyncSession)
        self.indexer_version = indexer_version

    async def delete_documents(self, uris: list[str]) -> None:
        async with self.session_factory() as session, session.begin():
            # this should delete attached documents thanks to ON DELETE CASCADE
            await session.execute(delete(TableDocument).where(TableDocument.uri.in_(uris)))
            await session.commit()

    async def create_indexed_documents(self, uris: list[str]) -> dict[str, UUID]:
        now = datetime.now(tz=dt.timezone.utc)

        uri_to_id: dict[str, UUID] = {}
        async with self.session_factory() as session, session.begin():
            for uri in uris:
                smt =  insert(TableDocument).values(id=uuid7(), uri=uri, creation_datetime=now)
                smt = smt.on_conflict_do_nothing(index_elements=[TableDocument.uri]).returning(TableDocument.id)
                id = await session.execute(smt)
                uri_to_id[uri] = id.scalar_one()

            documents = [
                TableIndexedDocument(
                    id=uuid7(),  # Generate a unique UUID for each document
                    source_document_id=uri_to_id[uri],
                    indexed_source_version=None,
                    indexed_content_id=None,
                    status=TableDocumentStatusEnum.pending,
                    last_status_change=now,
                    error_status_message=None,
                    indexer_version=self.indexer_version,
                    creation_datetime=now,
                )
                for uri in uris
            ]

            session.add_all(documents)
            await session.commit()
        return uri_to_id

    async def update_indexed_documents_status(
        self,
        uris: list[str],
        status: TableDocumentStatusEnum,
        error_status_message: str | None,
    ) -> None:
        now = datetime.now(tz=dt.timezone.utc)

        async with self.session_factory() as session, session.begin():
            # see. https://docs.sqlalchemy.org/en/20/tutorial/data_update.html#update-from
            await session.execute(
                update(TableIndexedDocument)
                .where(TableIndexedDocument.document_id == TableDocument.id)
                .where(TableDocument.uri.in_(uris))
                .where(TableIndexedDocument.indexer_version == self.indexer_version)
                .values(status=status, last_status_change=now, error_status_message=error_status_message),
            )
            await session.commit()


    async def get_indexed_content_if_exists(self, raw_hash: str) -> tuple[UUID, DbIndexedContent] | None:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(TableIndexedContent)
                .where(TableIndexedContent.raw_hash == raw_hash)
                .where(TableIndexedContent.indexer_version == self.indexer_version),
            )
            content = result.scalar_one_or_none()
            return (
                (
                    content.id,
                    DbIndexedContent(
                        raw_hash=content.raw_hash,
                        parsed_hash=content.parsed_hash,
                        last_indexing=content.last_indexing,
                    ),
                )
                if content
                else None
            )

    async def upsert_indexed_content(self, indexed_content: DbIndexedContent) -> UUID:
        # create an indexed_content or update it if one with the same raw_hash already exists
        async with self.session_factory() as session, session.begin():
TODO HERE MANAGE NEW REF URI AND INDEXER_VERSION
TODO: check indexer_version managed everywhere
            stmt = insert(TableIndexedContent).values(
                id=uuid7(),
                raw_hash=indexed_content.raw_hash,
                parsed_hash=indexed_content.parsed_hash,
                last_indexing=indexed_content.last_indexing,
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=[TableIndexedContent.raw_hash],
                set_={
                    TableIndexedContent.parsed_hash: indexed_content.parsed_hash,
                    TableIndexedContent.last_indexing: indexed_content.last_indexing,
                },
            ).returning(TableIndexedContent.id)

            result = await session.execute(stmt)
            uuid = result.scalar_one()
            await session.commit()
            return uuid

    async def update_document_indexed_content(
        self,
        uri: str,
        indexed_source_version: str | None,
        indexed_content_id: UUID,
    ) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(
                update(TableIndexedDocument)
                .where(TableIndexedDocument.uri == uri)
                .values(
                    status=TableDocumentStatusEnum.indexing_success,
                    last_status_change=datetime.now(tz=dt.timezone.utc),
                    error_status_message=None,
                    indexed_source_version=indexed_source_version,
                    indexed_content_id=indexed_content_id,
                ),
            )

            await session.commit()

    async def get_documents_from_indexed_parsed_hashes(
        self,
        parsed_hashes: list[str],
    ) -> dict[str, DbDocument]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TableIndexedDocument, TableIndexedContent)
                .where(TableIndexedContent.parsed_hash.in_(parsed_hashes))
                .join(TableIndexedContent, TableIndexedDocument.indexed_content_id == TableIndexedContent.id),
            )

            table_rows = result.all()
            plain_objs = {row[1].parsed_hash: to_doc(row[0], row[1]) for row in table_rows}

            return plain_objs

    async def get_all_documents(self) -> list[DbDocument]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TableIndexedDocument, TableIndexedContent).outerjoin(
                    TableIndexedContent,
                    TableIndexedDocument.indexed_content_id == TableIndexedContent.id,
                ),
            )

            table_rows = result.all()
            plain_objs = [to_doc(row[0], row[1]) for row in table_rows]

            return plain_objs

    async def get_documents(self, uris: list[str]) -> dict[str, DbDocument]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TableIndexedDocument, TableIndexedContent)
                .where(TableIndexedDocument.uri.in_(uris))
                .outerjoin(TableIndexedContent, TableIndexedDocument.indexed_content_id == TableIndexedContent.id),
            )

            table_rows = result.all()
            plain_objs = {row[0].uri: to_doc(row[0], row[1]) for row in table_rows}

            return plain_objs
