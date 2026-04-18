from datetime import date
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundError
from app.models.book import Book
from app.services.book import BookService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(mock_repo: AsyncMock) -> BookService:
    return BookService(repo=mock_repo)


@pytest.fixture
def db() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_book() -> Book:
    return Book(
        id=1,
        title="O Hobbit",
        author="J.R.R. Tolkien",
        published_date=date(1937, 9, 21),
    )


class TestCreate:
    async def test_delegates_to_repo(
        self,
        service: BookService,
        mock_repo: AsyncMock,
        db: AsyncMock,
        sample_book: Book,
    ) -> None:
        mock_repo.create.return_value = sample_book
        result = await service.create(db, title="O Hobbit", author="Tolkien")
        assert result is sample_book
        mock_repo.create.assert_awaited_once_with(db, title="O Hobbit", author="Tolkien")


class TestGet:
    async def test_returns_book_when_found(
        self,
        service: BookService,
        mock_repo: AsyncMock,
        db: AsyncMock,
        sample_book: Book,
    ) -> None:
        mock_repo.get.return_value = sample_book
        assert await service.get(db, 1) is sample_book

    async def test_raises_when_missing(
        self, service: BookService, mock_repo: AsyncMock, db: AsyncMock
    ) -> None:
        mock_repo.get.return_value = None
        with pytest.raises(BookNotFoundError, match="999"):
            await service.get(db, 999)


class TestList:
    async def test_passes_all_filters_to_repo(
        self, service: BookService, mock_repo: AsyncMock, db: AsyncMock
    ) -> None:
        mock_repo.list.return_value = ([], 0)
        await service.list(
            db,
            title="hobbit",
            author="tolkien",
            skip=5,
            limit=10,
            sort_by="title",
            order="asc",
        )
        mock_repo.list.assert_awaited_once_with(
            db,
            title="hobbit",
            author="tolkien",
            skip=5,
            limit=10,
            sort_by="title",
            order="asc",
        )

    async def test_default_ordering_is_created_at_desc(
        self, service: BookService, mock_repo: AsyncMock, db: AsyncMock
    ) -> None:
        mock_repo.list.return_value = ([], 0)
        await service.list(db)
        _, kwargs = mock_repo.list.call_args
        assert kwargs["sort_by"] == "created_at"
        assert kwargs["order"] == "desc"


class TestUpdate:
    async def test_returns_updated_book(
        self,
        service: BookService,
        mock_repo: AsyncMock,
        db: AsyncMock,
        sample_book: Book,
    ) -> None:
        mock_repo.update.return_value = sample_book
        result = await service.update(db, 1, summary="new")
        assert result is sample_book
        mock_repo.update.assert_awaited_once_with(db, 1, summary="new")

    async def test_raises_when_missing(
        self, service: BookService, mock_repo: AsyncMock, db: AsyncMock
    ) -> None:
        mock_repo.update.return_value = None
        with pytest.raises(BookNotFoundError, match="999"):
            await service.update(db, 999, summary="ghost")


class TestDelete:
    async def test_delegates_when_exists(
        self, service: BookService, mock_repo: AsyncMock, db: AsyncMock
    ) -> None:
        mock_repo.delete.return_value = True
        await service.delete(db, 1)
        mock_repo.delete.assert_awaited_once_with(db, 1)

    async def test_raises_when_missing(
        self, service: BookService, mock_repo: AsyncMock, db: AsyncMock
    ) -> None:
        mock_repo.delete.return_value = False
        with pytest.raises(BookNotFoundError, match="999"):
            await service.delete(db, 999)
