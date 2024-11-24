from datetime import datetime
from uuid import UUID

from sqlalchemy import MetaData, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from app.model import DocumentSnippet

DATABASE_URL = "postgresql+asyncpg://seemantic_back:seemantic_back_test_pwd@localhost:5432/postgres"


DbBase = declarative_base(metadata=MetaData(schema="seemantic_schema"))


class DbDocumentSnippet(DbBase):
    __tablename__ = "document_snippet"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    relative_path: Mapped[str]
    last_modification_datetime: Mapped[datetime]
    content_sha256: Mapped[str]


class ResourceConflictError(Exception):
    """Raised when a unique constraint is violated."""


class DbService:

    def __init__(self) -> None:
        pass

    engine = create_async_engine(DATABASE_URL, echo=True)

    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async def create_document_snippet(self, document_snippet: DocumentSnippet) -> DocumentSnippet:
        async with self.session_factory() as session:
            async with session.begin():
                try:
                    db_doc = self._to_db_document_snippet(document_snippet)
                    session.add(db_doc)
                    await session.commit()
                    return document_snippet
                except IntegrityError:
                    raise ResourceConflictError(f"Document at path '{document_snippet.relative_path}' already exists")

    def _to_db_document_snippet(self, document_snippet: DocumentSnippet) -> DbDocumentSnippet:
        return DbDocumentSnippet(id=document_snippet.id, relative_path=document_snippet.relative_path, last_modification_datetime=datetime.now(), content_sha256=document_snippet.content_sha256)


    async def update_document_snippet(self, document_snippet: DocumentSnippet) -> DocumentSnippet:
        db_snippet: DbDocumentSnippet = self._to_db_document_snippet(document_snippet)
        update_dict = {col: getattr(db_snippet, col) for col in DbDocumentSnippet.__table__.columns.keys()}
        
        async with self.session_factory() as session:
            async with session.begin():
                stmt = update(DbDocumentSnippet).where(DbDocumentSnippet.id == document_snippet.id).values(update_dict)
                await session.execute(stmt)
                await session.commit()
                return document_snippet
