from collections.abc import Awaitable, Callable
from typing import Any, List  # noqa: UP035  (builtin `list` shadowed by method)

import numpy as np
from openai import APIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import (
    build_book_text,
    bulk_cosine,
    deserialize_embedding,
    generate_embedding,
)
from app.ai.summary import generate_summary
from app.config import get_settings
from app.core.exceptions import BookNotFoundError, LLMUnavailableError
from app.models.book import Book, SummarySource
from app.repositories.book import BookRepository, SortField, SortOrder, book_repository

SummaryGenerator = Callable[[str, str], Awaitable[str]]
EmbeddingGenerator = Callable[[str], Awaitable[bytes]]

EMBEDDING_FIELDS = frozenset({"title", "author", "summary"})


class BookService:
    def __init__(
        self,
        repo: BookRepository | None = None,
        summary_generator: SummaryGenerator | None = None,
        embedding_generator: EmbeddingGenerator | None = None,
    ) -> None:
        self.repo = repo or book_repository
        self.summary_generator: SummaryGenerator = summary_generator or generate_summary
        self.embedding_generator: EmbeddingGenerator = embedding_generator or generate_embedding

    async def create(self, db: AsyncSession, **data: Any) -> Book:
        if self._should_auto_summarize(data):
            data = await self._enrich_with_summary(data)
        if self._ai_available():
            data = await self._enrich_with_embedding(data)
        return await self.repo.create(db, **data)

    def _ai_available(self) -> bool:
        settings = get_settings()
        return settings.ai_features_enabled and bool(settings.openrouter_api_key)

    def _should_auto_summarize(self, data: dict[str, Any]) -> bool:
        return self._ai_available() and not data.get("summary")

    async def _enrich_with_summary(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            generated = await self.summary_generator(data["title"], data["author"])
        except (LLMUnavailableError, APIError):
            return data

        if generated:
            data["summary"] = generated
            data["summary_source"] = SummarySource.AI
        return data

    async def _enrich_with_embedding(self, data: dict[str, Any]) -> dict[str, Any]:
        text = build_book_text(data["title"], data["author"], data.get("summary"))
        try:
            embedding = await self.embedding_generator(text)
        except (LLMUnavailableError, APIError):
            return data

        data["embedding"] = embedding
        data["embedding_model"] = get_settings().openrouter_embedding_model
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

        if EMBEDDING_FIELDS & data.keys() and self._ai_available():
            book = await self._refresh_embedding(db, book)
        return book

    async def _refresh_embedding(self, db: AsyncSession, book: Book) -> Book:
        text = build_book_text(book.title, book.author, book.summary)
        try:
            embedding = await self.embedding_generator(text)
        except (LLMUnavailableError, APIError):
            return book

        refreshed = await self.repo.update(
            db,
            book.id,
            embedding=embedding,
            embedding_model=get_settings().openrouter_embedding_model,
        )
        return refreshed or book

    async def delete(self, db: AsyncSession, book_id: int) -> None:
        deleted = await self.repo.delete(db, book_id)
        if not deleted:
            raise BookNotFoundError(f"Book with id {book_id} not found")

    async def semantic_search(
        self,
        db: AsyncSession,
        query: str,
        *,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[tuple[Book, float]]:  # noqa: UP006
        books = await self.repo.list_with_embeddings(db)
        if not books:
            return []

        try:
            query_bytes = await self.embedding_generator(query)
        except APIError as e:
            raise LLMUnavailableError(f"embedding service unavailable: {e}") from e

        query_vec = deserialize_embedding(query_bytes)
        matrix = np.vstack([deserialize_embedding(b.embedding) for b in books if b.embedding])
        scores = bulk_cosine(query_vec, matrix)

        pairs = [
            (book, float(score))
            for book, score in zip(books, scores, strict=True)
            if score >= min_score
        ]
        pairs.sort(key=lambda p: p[1], reverse=True)
        return pairs[:top_k]


book_service = BookService()
