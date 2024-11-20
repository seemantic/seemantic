from app.model import DocumentSnippet

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
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



class DbService:

    def __init__(self) -> None:
        pass

    engine = create_async_engine(DATABASE_URL, echo=True)

    session_factory = sessionmaker(engine, class_=AsyncSession) # type: ignore


    async def create_document_snippet(self, document_snippet: DocumentSnippet):
        async with self.session_factory() as session:
            async with session.begin():
                db_doc = DbDocumentSnippet(id=document_snippet.id, relative_path=document_snippet.relative_path, last_modification_datetime=datetime.now())
                session.add(db_doc)
                await session.commit()
                return document_snippet
