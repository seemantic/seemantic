from datetime import datetime
from typing import cast
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import TIMESTAMP, MetaData, delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
import enum


class DbSettings(BaseModel, frozen=True):
    username: str
    password: str
    host: str
    port: int
    database: str


Base = declarative_base(metadata=MetaData(schema="seemantic_schema"))


class TableDocumentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    INDEXING_SUCCESS = "indexing_success"
    INDEXING_ERROR = "indexing_error"

class TableDocument(Base):
    __tablename__ = "document"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(nullable=False, unique=True)
    
    # version
    source_specific_current_version_id: Mapped[str | None] = mapped_column(nullable=True)
    current_version_raw_hash: Mapped[str | None] = mapped_column(nullable=True)
    last_modification: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # indexing
    last_indexed_version_raw_hash: Mapped[str | None] = mapped_column(nullable=True)
    last_indexing: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # status
    status: Mapped[TableDocumentStatusEnum] = mapped_column(nullable=False)
    last_status_change: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    error_status_message: Mapped[str] = mapped_column(nullable=True)
    
    creation_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)



class DbDocumentId(BaseModel):
    uri: str

class DbDocumentVersion(BaseModel):
    source_specific_id: str | None
    raw_hash: str
    last_modification: datetime

class DbDocumentIndexedVersion(BaseModel):
    raw_hash: str
    last_modification: datetime

class DbDocumentStatus(BaseModel):
    status: TableDocumentStatusEnum
    last_status_change: datetime
    error_status_message: str | None


class DbDocument(BaseModel):
    uri: str
    current_version: DbDocumentVersion | None
    indexed_version: DbDocumentIndexedVersion | None
    status: DbDocumentStatus
    



def to_doc(table_obj: TableDocument) -> DbDocument:

    current_version = DbDocumentVersion(
            source_specific_id=table_obj.source_specific_current_version_id,
            raw_hash=table_obj.current_version_raw_hash,
            last_modification=cast(datetime,table_obj.last_modification),
        ) if table_obj.current_version_raw_hash is not None else None
    

    indexed_version = DbDocumentIndexedVersion(
            raw_hash=table_obj.last_indexed_version_raw_hash,
            last_modification=cast(datetime,table_obj.last_indexing),
        ) if table_obj.last_indexed_version_raw_hash is not None else None

    return DbDocument(
        uri=table_obj.uri,
        current_version=current_version,        
        indexed_version=indexed_version,
        status=DbDocumentStatus(
            status=table_obj.status,
            last_status_change=table_obj.last_status_change,
            error_status_message=table_obj.error_status_message
        )
    )




class DbService:

    def __init__(self, settings: DbSettings) -> None:
        url = f"postgresql+asyncpg://{settings.username}:{settings.password}@{settings.host}:{settings.port}/{settings.database}"
        engine = create_async_engine(url, echo=True)
        self.session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async def delete_source_documents(self, uris: list[str]) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(delete(TableDocument).where(TableDocument.uri.in_(uris)))
            await session.commit()

    async def get_documents_from_indexed_raw_hashes(
        self,
        raw_hashes: list[str],
    ) -> list[DbDocument]:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(TableDocument)
                .where(TableDocument.last_indexed_version_raw_hash.in_(raw_hashes)),
            )

            table_rows = result.all()
            plain_objs = [to_doc(row[0]) for row in table_rows]

            return plain_objs


    async def get_all_documents(self) -> list[DbDocument]:
        async with self.session_factory() as session, session.begin():
            result = await session.execute(
                select(TableDocument),
            )

            table_rows = result.all()
            plain_objs = [to_doc(row[0]) for row in table_rows]

            return plain_objs




