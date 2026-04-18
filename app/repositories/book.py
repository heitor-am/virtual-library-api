from typing import Any, List, Literal  # noqa: UP035  (builtin `list` shadowed by method)

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book

SortField = Literal["title", "author", "published_date", "created_at"]
SortOrder = Literal["asc", "desc"]


class BookRepository:
    async def create(self, db: AsyncSession, **data: Any) -> Book:
        book = Book(**data)
        db.add(book)
        await db.commit()
        await db.refresh(book)
        return book

    async def get(self, db: AsyncSession, book_id: int) -> Book | None:
        return await db.get(Book, book_id)

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
        stmt = select(Book)
        count_stmt = select(func.count()).select_from(Book)

        if title:
            pattern = f"%{title.lower()}%"
            stmt = stmt.where(func.lower(Book.title).like(pattern))
            count_stmt = count_stmt.where(func.lower(Book.title).like(pattern))

        if author:
            pattern = f"%{author.lower()}%"
            stmt = stmt.where(func.lower(Book.author).like(pattern))
            count_stmt = count_stmt.where(func.lower(Book.author).like(pattern))

        sort_col = getattr(Book, sort_by)
        stmt = stmt.order_by(sort_col.asc() if order == "asc" else sort_col.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        return items, total

    async def update(self, db: AsyncSession, book_id: int, **data: Any) -> Book | None:
        book = await db.get(Book, book_id)
        if book is None:
            return None

        for key, value in data.items():
            setattr(book, key, value)

        await db.commit()
        await db.refresh(book)
        return book

    async def list_with_embeddings(self, db: AsyncSession) -> List[Book]:  # noqa: UP006
        stmt = select(Book).where(Book.embedding.is_not(None))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, db: AsyncSession, book_id: int) -> bool:
        book = await db.get(Book, book_id)
        if book is None:
            return False
        await db.delete(book)
        await db.commit()
        return True


book_repository = BookRepository()
