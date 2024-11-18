from os import path
from typing import Optional, List
from app.model import Document, DocumentSnippet

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, MetaData, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base

DATABASE_URL = "postgresql+asyncpg://seemantic_back:seemantic_back_test_pwd@localhost:5432/postgres"


DbBase = declarative_base(metadata=MetaData(schema="seemantic_schema"))


class DbDocumentSnippet(DbBase):
    __tablename__ = "document_snippet"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    uri: Mapped[str]



class DbService:

    def __init__(self) -> None:
        pass

    engine = create_async_engine(DATABASE_URL, echo=True)

    session_factory = sessionmaker(engine, class_=AsyncSession) # type: ignore


    async def create_document_snippet(self, document_snippet: DocumentSnippet):
        async with self.session_factory() as session:
            async with session.begin():
                db_doc = DbDocumentSnippet(id=document_snippet.id, uri=document_snippet.uri)
                session.add(db_doc)
                await session.commit()
                return document_snippet
