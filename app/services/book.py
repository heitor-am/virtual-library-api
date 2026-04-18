from collections.abc import Awaitable, Callable
from typing import Any

from openai import APIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.summary import generate_summary
from app.config import get_settings
from app.core.exceptions import BookNotFoundError, LLMUnavailableError
from app.models.book import Book, SummarySource
from app.repositories.book import BookRepository, SortField, SortOrder, book_repository

SummaryGenerator = Callable[[str, str], Awaitable[str]]


class BookService:
    def __init__(
        self,
        repo: BookRepository | None = None,
        summary_generator: SummaryGenerator | None = None,
    ) -> None:
        self.repo = repo or book_repository
        self.summary_generator: SummaryGenerator = summary_generator or generate_summary

    async def create(self, db: AsyncSession, **data: Any) -> Book:
        if self._should_auto_summarize(data):
            data = await self._enrich_with_summary(data)
        return await self.repo.create(db, **data)

    def _should_auto_summarize(self, data: dict[str, Any]) -> bool:
        settings = get_settings()
        return (
            settings.ai_features_enabled
            and bool(settings.openrouter_api_key)
            and not data.get("summary")
        )

    async def _enrich_with_summary(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            generated = await self.summary_generator(data["title"], data["author"])
        except (LLMUnavailableError, APIError):
            return data

        if generated:
            data["summary"] = generated
            data["summary_source"] = SummarySource.AI
        return data

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
