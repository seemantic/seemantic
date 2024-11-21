from app.model import DocumentSnippet
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base
from datetime import datetime
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
    pass

class DbService:

    def __init__(self) -> None:
        pass

    engine = create_async_engine(DATABASE_URL, echo=True)

    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async def create_document_snippet(self, document_snippet: DocumentSnippet) -> DocumentSnippet:
        async with self.session_factory() as session:
            async with session.begin():
                try:
                    db_doc = DbDocumentSnippet(id=document_snippet.id, relative_path=document_snippet.relative_path, last_modification_datetime=datetime.now(), content_sha256=document_snippet.content_sha256)
                    session.add(db_doc)
                    await session.commit()
                    return document_snippet
                except IntegrityError:
                    raise ResourceConflictError(f"Document at path '{document_snippet.relative_path}' already exists")


