import datetime as dt
import enum
from datetime import datetime
from typing import cast
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import TIMESTAMP, Enum, MetaData, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from uuid_utils import uuid7


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


class TableDocument(Base):
    __tablename__ = "document"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(nullable=False, unique=True)

    # version
    indexed_source_version: Mapped[str | None] = mapped_column(nullable=True)
    indexed_version_raw_hash: Mapped[str | None] = mapped_column(nullable=True)
    indexed_version_parsed_hash: Mapped[str | None] = mapped_column(nullable=True)

    last_indexing: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # status
    status: Mapped[TableDocumentStatusEnum] = mapped_column(
        Enum(TableDocumentStatusEnum, name="document_status"),
        nullable=False,
    )
    last_status_change: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    error_status_message: Mapped[str] = mapped_column(nullable=True)

    creation_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class DbDocumentIndexedVersion(BaseModel):
    source_version: str | None
    raw_hash: str
    parsed_hash: str
    last_modification: datetime


class DbDocumentStatus(BaseModel):
    status: TableDocumentStatusEnum
    last_status_change: datetime
    error_status_message: str | None


class DbDocument(BaseModel):
    uri: str
    indexed_version: DbDocumentIndexedVersion | None
    status: DbDocumentStatus


def to_doc(table_obj: TableDocument) -> DbDocument:

    indexed_version = (
        DbDocumentIndexedVersion(
            source_version=table_obj.indexed_source_version,
            raw_hash=table_obj.indexed_version_raw_hash,
            parsed_hash=cast(str, table_obj.indexed_version_parsed_hash),
            last_modification=cast(datetime, table_obj.last_indexing),
        )
        if table_obj.indexed_version_raw_hash is not None
        else None
    )

    return DbDocument(
        uri=table_obj.uri,
        indexed_version=indexed_version,
        status=DbDocumentStatus(
            status=table_obj.status,
            last_status_change=table_obj.last_status_change,
            error_status_message=table_obj.error_status_message,
        ),
    )


class DbService:

    def __init__(self, settings: DbSettings) -> None:
        url = f"postgresql+asyncpg://{settings.username}:{settings.password}@{settings.host}:{settings.port}/{settings.database}"
        engine = create_async_engine(url, echo=True)  # add connect_args={"timeout": 10} in production ?
        self.session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async def delete_documents(self, uris: list[str]) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(delete(TableDocument).where(TableDocument.uri.in_(uris)))
            await session.commit()

    async def create_documents(self, uris: list[str]) -> None:
        now = datetime.now(tz=dt.timezone.utc)
        async with self.session_factory() as session, session.begin():
            documents = [
                TableDocument(
                    id=uuid7(),  # Generate a unique UUID for each document
                    uri=uri,
                    indexed_source_version=None,
                    indexed_version_raw_hash=None,
                    indexed_version_parsed_hash=None,
                    last_indexing=None,
                    status=TableDocumentStatusEnum.pending,
                    last_status_change=now,
                    error_status_message=None,
                    creation_datetime=now,
                )
                for uri in uris
            ]

            session.add_all(documents)
            await session.commit()

    async def update_documents_status(
        self,
        uris: list[str],
        status: TableDocumentStatusEnum,
        error_status_message: str | None,
    ) -> None:
        now = datetime.now(tz=dt.timezone.utc)
        async with self.session_factory() as session, session.begin():
            await session.execute(
                update(TableDocument)
                .where(TableDocument.uri.in_(uris))
                .values(status=status, last_status_change=now, error_status_message=error_status_message),
            )
            await session.commit()

    async def update_documents_indexed_version(self, uri: str, indexed_version: DbDocumentIndexedVersion) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(
                update(TableDocument)
                .where(TableDocument.uri == uri)
                .values(
                    status=TableDocumentStatusEnum.indexing_success,
                    last_status_change=indexed_version.last_modification,
                    error_status_message=None,
                    indexed_source_version=indexed_version.source_version,
                    indexed_version_raw_hash=indexed_version.raw_hash,
                    indexed_version_parsed_hash=indexed_version.parsed_hash,
                    last_indexing=indexed_version.last_modification,
                ),
            )

            await session.commit()

    async def get_id(self, uris: list[str]) -> dict[str, UUID]:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(TableDocument.id, TableDocument.uri).where(TableDocument.uri.in_(uris)),
            )
            table_rows = result.all()
            return {row[1]: row[0] for row in table_rows}

    async def get_documents_from_indexed_parsed_hashes(
        self,
        parsed_hashes: list[str],
    ) -> dict[str, DbDocument]:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(TableDocument).where(TableDocument.indexed_version_parsed_hash.in_(parsed_hashes)),
            )

            table_rows = result.all()
            plain_objs = {row[0].indexed_version_parsed_hash: to_doc(row[0]) for row in table_rows}

            return plain_objs

    async def get_all_documents(self) -> list[DbDocument]:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(TableDocument),
            )

            table_rows = result.all()
            plain_objs = [to_doc(row[0]) for row in table_rows]

            return plain_objs

    async def get_documents(self, uris: list[str]) -> dict[str, DbDocument]:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(TableDocument).where(TableDocument.uri.in_(uris)),
            )

            table_rows = result.all()
            plain_objs = {row[0].uri: to_doc(row[0]) for row in table_rows}

            return plain_objs

    async def get_document(self, uri: str) -> DbDocument:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(TableDocument).where(TableDocument.uri == uri),
            )

            row = result.first()
            if not row:
                raise ValueError(f"Document {uri} not found")
            return to_doc(row[0])
