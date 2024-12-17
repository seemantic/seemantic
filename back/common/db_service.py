from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy import MetaData, delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from app.model import DocumentSnippet

DATABASE_URL = "postgresql+asyncpg://seemantic_back:seemantic_back_test_pwd@localhost:5432/postgres"


DbBase = declarative_base(metadata=MetaData(schema="seemantic_schema"))


class DbSourceDocument(DbBase):
    __tablename__ = "source_document"

    uri: Mapped[str] = mapped_column(primary_key=True)
    raw_content_hash: Mapped[str]
    last_crawling_datetime: Mapped[datetime]
    last_content_update_datetime: Mapped[datetime]

class DbRawDocument(DbBase):
    __tablename__ = "raw_document"

    raw_content_hash: Mapped[str] = mapped_column(primary_key=True)
    parsed_content_hash: Mapped[str]
    last_parsed_update_datetime: Mapped[datetime]



class ResourceConflictError(Exception):
    """Raised when a unique constraint is violated."""


class SourceDocument(BaseModel):
    uri: str
    raw_content_hash: str

class RawDocument(BaseModel):
    raw_content_hash: str
    parsed_content_hash: str


class DbService:

    def __init__(self) -> None:
        pass

    engine = create_async_engine(DATABASE_URL, echo=True)

    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async def update_crawling_datetime(self, uri: str, crawling_datetime: datetime) -> None:
        pass

    async def upsert_source_document(self, source_document: SourceDocument, crawling_datetime: datetime) -> None:
        async with self.session_factory() as session, session.begin():
            db_doc = DbSourceDocument(
                uri=source_document.uri,
                raw_content_hash=source_document.raw_content_hash,
                last_crawling_datetime=crawling_datetime,
                last_content_update_datetime=crawling_datetime,
            )
            await session.merge(db_doc)
            await session.commit()

    async def select_all_source_documents(self) -> list[SourceDocument]:
        async with self.session_factory() as session, session.begin():
            db_docs = await session.execute(select(DbSourceDocument))
            return [SourceDocument(uri=db_doc.uri, raw_content_hash=db_doc.raw_content_hash) for db_doc in db_docs.scalars()]


    async def delete_source_documents(self, uris: list[str]) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(
                delete(DbSourceDocument).where(DbSourceDocument.uri.in_(uris))
            )
            await session.commit()


    async def create_document_snippet(
        self, document_snippet: DocumentSnippet,
    ) -> DocumentSnippet:
        async with self.session_factory() as session, session.begin():
            try:
                db_doc = self._to_db_document_snippet(document_snippet)
                session.add(db_doc)
                await session.commit()
            except IntegrityError as exc:
                raise ResourceConflictError(
                    f"Document at path '{document_snippet.relative_path}' already exists"
                ) from exc
            else:
                return document_snippet



    def _to_db_document_snippet(
        self, document_snippet: DocumentSnippet
    ) -> DbDocumentSnippet:
        return DbDocumentSnippet(
            id=document_snippet.id,
            relative_path=document_snippet.relative_path,
            last_modification_datetime=datetime.now(tz=timezone.utc),
            content_sha256=document_snippet.content_sha256,
        )

    async def update_document_snippet(
        self, document_snippet: DocumentSnippet
    ) -> DocumentSnippet:
        db_snippet: DbDocumentSnippet = self._to_db_document_snippet(document_snippet)
        update_dict = {
            col: getattr(db_snippet, col) for col in DbDocumentSnippet.__table__.columns
        }

        async with self.session_factory() as session, session.begin():
            stmt = (
                update(DbDocumentSnippet)
                .where(DbDocumentSnippet.id == document_snippet.id)
                .values(update_dict)
            )
            await session.execute(stmt)
            await session.commit()
            return document_snippet

