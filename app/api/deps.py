from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.book import BookService, book_service


def get_book_service() -> BookService:
    return book_service


DbDep = Annotated[AsyncSession, Depends(get_db)]
BookServiceDep = Annotated[BookService, Depends(get_book_service)]
