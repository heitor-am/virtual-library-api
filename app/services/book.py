from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundError
from app.models.book import Book
from app.repositories.book import BookRepository, SortField, SortOrder, book_repository


class BookService:
    def __init__(self, repo: BookRepository | None = None) -> None:
        self.repo = repo or book_repository

    async def create(self, db: AsyncSession, **data: Any) -> Book:
        return await self.repo.create(db, **data)

    async def get(self, db: AsyncSession, book_id: int) -> Book:
        book = await self.repo.get(db, book_id)
        if book is None:
            raise BookNotFoundError(f"Book with id {book_id} not found")
        return book

    async def list(
        self,
        db: AsyncSession,
        *,
        title: str | None = None,
        author: str | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: SortField = "created_at",
        order: SortOrder = "desc",
    ) -> tuple[list[Book], int]:
        return await self.repo.list(
            db,
            title=title,
            author=author,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            order=order,
        )

    async def update(self, db: AsyncSession, book_id: int, **data: Any) -> Book:
        book = await self.repo.update(db, book_id, **data)
        if book is None:
            raise BookNotFoundError(f"Book with id {book_id} not found")
        return book

    async def delete(self, db: AsyncSession, book_id: int) -> None:
        deleted = await self.repo.delete(db, book_id)
        if not deleted:
            raise BookNotFoundError(f"Book with id {book_id} not found")


book_service = BookService()
