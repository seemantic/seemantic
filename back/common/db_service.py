import asyncio
import datetime as dt
import enum
from datetime import datetime
from typing import Set
from uuid import UUID

import asyncpg
from pydantic import BaseModel
from sqlalchemy import TIMESTAMP, Enum, ForeignKey, MetaData, delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from uuid_utils.compat import (
    uuid7,
)  # cf. https://pypi.org/project/uuid-utils/ compat so that instances are real UUIDs form std lib (else pydantic complains)


class DbSettings(BaseModel, frozen=True):
    username: str
    password: str
    host: str
    port: int
    database: str


Base = declarative_base(metadata=MetaData(schema="seemantic_schema"))


class TableIndexedDocumentStatusEnum(enum.Enum):
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
    indexer_version: Mapped[int] = mapped_column(nullable=False)


class TableDocument(Base):
    __tablename__ = "document"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(nullable=False, unique=True)
    creation_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class TableIndexedDocument(Base):
    __tablename__ = "indexed_document"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(nullable=False)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("document.id"), nullable=False)

    # version
    indexed_source_version: Mapped[str | None] = mapped_column(nullable=True)
    indexed_content_id: Mapped[UUID | None] = mapped_column(ForeignKey("indexed_content.id"), nullable=True)
    indexer_version: Mapped[int] = mapped_column(nullable=False)
    last_indexing: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )  # updated when indexed_content_id is updated

    # status
    status: Mapped[TableIndexedDocumentStatusEnum] = mapped_column(
        Enum(TableIndexedDocumentStatusEnum, name="document_status"),
        nullable=False,
    )
    last_status_change: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    error_status_message: Mapped[str] = mapped_column(nullable=True)

    creation_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class DbIndexedContent(BaseModel):
    raw_hash: str
    parsed_hash: str


class DbDocumentStatus(BaseModel):
    status: TableIndexedDocumentStatusEnum
    last_status_change: datetime
    error_status_message: str | None


class DbDocument(BaseModel):
    uri: str
    indexed_document_id: UUID
    indexed_source_version: str | None
    status: DbDocumentStatus
    last_indexing: datetime | None


def to_doc(row_indexed_doc: TableIndexedDocument) -> DbDocument:

    return DbDocument(
        uri=row_indexed_doc.uri,
        indexed_document_id=row_indexed_doc.id,
        indexed_source_version=row_indexed_doc.indexed_source_version,
        last_indexing=row_indexed_doc.last_indexing,
        status=DbDocumentStatus(
            status=row_indexed_doc.status,
            last_status_change=row_indexed_doc.last_status_change,
            error_status_message=row_indexed_doc.error_status_message,
        ),
    )


class DbService:

    indexer_version: int
    url: str
    session_factory: async_sessionmaker[AsyncSession]

    def __init__(self, settings: DbSettings) -> None:
        self.url = f"postgresql+asyncpg://{settings.username}:{settings.password}@{settings.host}:{settings.port}/{settings.database}"
        self.raw_url = f"postgresql://{settings.username}:{settings.password}@{settings.host}:{settings.port}/{settings.database}"
        engine = create_async_engine(self.url, echo=True)  # add connect_args={"timeout": 10} in production ?
        self.session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async def delete_documents(self, uris: list[str]) -> None:
        async with self.session_factory() as session, session.begin():
            # this should delete attached documents thanks to ON DELETE CASCADE
            await session.execute(delete(TableDocument).where(TableDocument.uri.in_(uris)))
            await session.commit()

    async def create_indexed_documents(self, uris: list[str], indexer_version: int) -> dict[str, UUID]:
        now = datetime.now(tz=dt.timezone.utc)

        uri_to_id: dict[str, UUID] = {}
        async with self.session_factory() as session, session.begin():
            for uri in uris:
                smt = insert(TableDocument).values(id=uuid7(), uri=uri, creation_datetime=now)
                # if uri already exists, this is a no op and the id is returned
                smt = smt.on_conflict_do_update(
                    index_elements=[TableDocument.uri],
                    set_={TableDocument.uri: uri},
                ).returning(TableDocument.id)
                id = await session.execute(smt)
                uri_to_id[uri] = id.scalar_one()

            uri_to_indexed_documents = {
                uri: TableIndexedDocument(
                    id=uuid7(),  # Generate a unique UUID for each document
                    uri=uri,
                    document_id=uri_to_id[uri],
                    indexed_source_version=None,
                    indexed_content_id=None,
                    last_indexing=None,
                    status=TableIndexedDocumentStatusEnum.pending,
                    last_status_change=now,
                    error_status_message=None,
                    indexer_version=indexer_version,
                    creation_datetime=now,
                )
                for uri in uris
            }

            session.add_all(uri_to_indexed_documents.values())
            result = {uri: indexed_doc.id for uri, indexed_doc in uri_to_indexed_documents.items()}
            await session.commit()

        return result

    async def update_indexed_documents_status(
        self,
        ids: list[UUID],
        status: TableIndexedDocumentStatusEnum,
        error_status_message: str | None,
    ) -> None:
        now = datetime.now(tz=dt.timezone.utc)

        async with self.session_factory() as session, session.begin():
            # see. https://docs.sqlalchemy.org/en/20/tutorial/data_update.html#update-from
            await session.execute(
                update(TableIndexedDocument)
                .where(TableIndexedDocument.id.in_(ids))
                .values(status=status, last_status_change=now, error_status_message=error_status_message),
            )
            await session.commit()

    async def get_indexed_content_if_exists(
        self,
        raw_hash: str,
        indexer_version: int,
    ) -> tuple[UUID, DbIndexedContent] | None:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(TableIndexedContent)
                .where(TableIndexedContent.raw_hash == raw_hash)
                .where(TableIndexedContent.indexer_version == indexer_version),
            )
            content = result.scalar_one_or_none()
            return (
                (
                    content.id,
                    DbIndexedContent(raw_hash=content.raw_hash, parsed_hash=content.parsed_hash),
                )
                if content
                else None
            )

    async def upsert_indexed_content(self, indexed_content: DbIndexedContent, indexer_version: int) -> UUID:
        # create an indexed_content or update it if one with the same raw_hash already exists
        async with self.session_factory() as session, session.begin():
            stmt = insert(TableIndexedContent).values(
                id=uuid7(),
                raw_hash=indexed_content.raw_hash,
                parsed_hash=indexed_content.parsed_hash,
                indexer_version=indexer_version,
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=[TableIndexedContent.raw_hash, TableIndexedContent.indexer_version],
                set_={
                    TableIndexedContent.parsed_hash: indexed_content.parsed_hash,
                },
            ).returning(TableIndexedContent.id)

            result = await session.execute(stmt)
            uuid = result.scalar_one()
            await session.commit()
            return uuid

    async def update_indexed_document_indexed_content_id(
        self,
        indexed_document_id: UUID,
        indexed_source_version: str | None,
        indexed_content_id: UUID,
    ) -> None:
        now = datetime.now(tz=dt.timezone.utc)
        async with self.session_factory() as session, session.begin():
            await session.execute(
                update(TableIndexedDocument)
                .where(TableIndexedDocument.id == indexed_document_id)
                .values(
                    status=TableIndexedDocumentStatusEnum.indexing_success,
                    last_status_change=now,
                    last_indexing=now,
                    error_status_message=None,
                    indexed_source_version=indexed_source_version,
                    indexed_content_id=indexed_content_id,
                ),
            )

            await session.commit()

    async def get_documents_from_indexed_parsed_hashes(
        self,
        parsed_hashes: list[str],
        indexer_version: int,
    ) -> dict[str, DbDocument]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TableIndexedDocument)
                .where(TableIndexedContent.parsed_hash.in_(parsed_hashes))
                .where(TableIndexedContent.indexer_version == indexer_version)
                .where(TableIndexedDocument.indexer_version == indexer_version)
                .join(TableIndexedContent, TableIndexedDocument.indexed_content_id == TableIndexedContent.id),
            )

            table_rows = result.all()
            plain_objs = {row[2].parsed_hash: to_doc(row[0]) for row in table_rows}

            return plain_objs

    async def get_all_documents(self, indexer_version: int) -> list[DbDocument]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TableIndexedDocument).where(TableIndexedDocument.indexer_version == indexer_version),
            )

            table_rows = result.all()
            plain_objs = [to_doc(row[0]) for row in table_rows]

            return plain_objs

    async def get_documents(self, uris: list[str], indexer_version: int) -> dict[str, DbDocument]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TableIndexedDocument)
                .where(TableIndexedDocument.uri.in_(uris))
                .where(TableIndexedDocument.indexer_version == indexer_version),
            )

            table_rows = result.all()
            plain_objs = {row[0].uri: to_doc(row[0]) for row in table_rows}

            return plain_objs


    subscribed_clients: Set[asyncio.Queue[str]] = set()
    connection: asyncpg.Connection | None = None

    async def listen_to_indexed_documents_changes(self, queue: asyncio.Queue[str], indexer_version: int) -> None:

        # Define callback function to process notifications
        def on_notification(
            conn: asyncpg.Connection, 
            pid: int, 
            channel: str, 
            payload: str
        ) -> None:
            for queue in DbService.subscribed_clients:
                if not queue.full():
                    queue.put_nowait(payload)

        self.subscribed_clients.add(queue)
        if not self.connection:
            connection: asyncpg.Connection = await asyncpg.connect(self.raw_url) # type: ignore
            self.connection = connection
            await connection.add_listener('table_changes', on_notification)
            await connection.execute('LISTEN table_changes')
        


    async def removed_listener_to_indexed_documents_changes(self, queue: asyncio.Queue[str]) -> None:
        self.subscribed_clients.remove(queue)
        if not self.subscribed_clients:
            connection: asyncpg.Connection | None = self.connection
            if connection is not None:
                try:
                    await connection.close() # this cleans all listeners
                except asyncio.CancelledError as e:
                    pass
                finally:
                    self.connection = None
