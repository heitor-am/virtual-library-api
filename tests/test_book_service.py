from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import APIConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import BookNotFoundError, LLMUnavailableError
from app.models.book import Book, SummarySource
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


class TestAutoSummarize:
    @pytest.fixture(autouse=True)
    def _ai_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("AI_FEATURES_ENABLED", "true")
        get_settings.cache_clear()

    async def test_generates_summary_when_missing(
        self, mock_repo: AsyncMock, db: AsyncMock, sample_book: Book
    ) -> None:
        mock_repo.create.return_value = sample_book
        summary_gen = AsyncMock(return_value="Aventura épica")
        service = BookService(repo=mock_repo, summary_generator=summary_gen)

        await service.create(
            db, title="O Hobbit", author="Tolkien", published_date=date(1937, 9, 21)
        )

        summary_gen.assert_awaited_once_with("O Hobbit", "Tolkien")
        _, kwargs = mock_repo.create.call_args
        assert kwargs["summary"] == "Aventura épica"
        assert kwargs["summary_source"] == SummarySource.AI

    async def test_skips_generation_when_summary_provided(
        self, mock_repo: AsyncMock, db: AsyncMock, sample_book: Book
    ) -> None:
        mock_repo.create.return_value = sample_book
        summary_gen = AsyncMock()
        service = BookService(repo=mock_repo, summary_generator=summary_gen)

        await service.create(
            db,
            title="O Hobbit",
            author="Tolkien",
            published_date=date(1937, 9, 21),
            summary="User-provided summary",
        )

        summary_gen.assert_not_awaited()
        _, kwargs = mock_repo.create.call_args
        assert kwargs["summary"] == "User-provided summary"
        assert "summary_source" not in kwargs

    async def test_skips_generation_when_disabled(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_repo: AsyncMock,
        db: AsyncMock,
        sample_book: Book,
    ) -> None:
        monkeypatch.setenv("AI_FEATURES_ENABLED", "false")
        get_settings.cache_clear()

        mock_repo.create.return_value = sample_book
        summary_gen = AsyncMock()
        service = BookService(repo=mock_repo, summary_generator=summary_gen)

        await service.create(
            db, title="O Hobbit", author="Tolkien", published_date=date(1937, 9, 21)
        )

        summary_gen.assert_not_awaited()

    async def test_skips_generation_when_api_key_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_repo: AsyncMock,
        db: AsyncMock,
        sample_book: Book,
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "")
        get_settings.cache_clear()

        mock_repo.create.return_value = sample_book
        summary_gen = AsyncMock()
        service = BookService(repo=mock_repo, summary_generator=summary_gen)

        await service.create(
            db, title="O Hobbit", author="Tolkien", published_date=date(1937, 9, 21)
        )

        summary_gen.assert_not_awaited()

    async def test_creates_book_even_when_llm_fails(
        self, mock_repo: AsyncMock, db: AsyncMock, sample_book: Book
    ) -> None:
        mock_repo.create.return_value = sample_book
        summary_gen = AsyncMock(
            side_effect=APIConnectionError(request=httpx.Request("POST", "https://openrouter.ai"))
        )
        service = BookService(repo=mock_repo, summary_generator=summary_gen)

        await service.create(
            db, title="O Hobbit", author="Tolkien", published_date=date(1937, 9, 21)
        )

        # Book is still created (AI error is swallowed)
        mock_repo.create.assert_awaited_once()
        _, kwargs = mock_repo.create.call_args
        assert "summary" not in kwargs
        assert "summary_source" not in kwargs

    async def test_creates_book_when_llm_unavailable(
        self, mock_repo: AsyncMock, db: AsyncMock, sample_book: Book
    ) -> None:
        mock_repo.create.return_value = sample_book
        summary_gen = AsyncMock(side_effect=LLMUnavailableError("no key"))
        service = BookService(repo=mock_repo, summary_generator=summary_gen)

        await service.create(
            db, title="O Hobbit", author="Tolkien", published_date=date(1937, 9, 21)
        )

        mock_repo.create.assert_awaited_once()


class TestEmbeddings:
    @pytest.fixture(autouse=True)
    def _ai_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("AI_FEATURES_ENABLED", "true")
        monkeypatch.setenv("OPENROUTER_EMBEDDING_MODEL", "baai/bge-m3")
        get_settings.cache_clear()

    async def test_create_stores_embedding(
        self, mock_repo: AsyncMock, db: AsyncMock, sample_book: Book
    ) -> None:
        mock_repo.create.return_value = sample_book
        summary_gen = AsyncMock(return_value="")
        embedding_gen = AsyncMock(return_value=b"\x00\x01\x02\x03")
        service = BookService(
            repo=mock_repo,
            summary_generator=summary_gen,
            embedding_generator=embedding_gen,
        )

        await service.create(
            db,
            title="O Hobbit",
            author="Tolkien",
            published_date=date(1937, 9, 21),
            summary="fixed summary",
        )

        _, kwargs = mock_repo.create.call_args
        assert kwargs["embedding"] == b"\x00\x01\x02\x03"
        assert kwargs["embedding_model"] == "baai/bge-m3"
        embedding_gen.assert_awaited_once()

    async def test_create_still_works_when_embedding_fails(
        self, mock_repo: AsyncMock, db: AsyncMock, sample_book: Book
    ) -> None:
        mock_repo.create.return_value = sample_book
        embedding_gen = AsyncMock(
            side_effect=APIConnectionError(request=httpx.Request("POST", "https://openrouter.ai"))
        )
        service = BookService(repo=mock_repo, embedding_generator=embedding_gen)

        await service.create(
            db,
            title="O Hobbit",
            author="Tolkien",
            published_date=date(1937, 9, 21),
            summary="s",
        )

        _, kwargs = mock_repo.create.call_args
        assert "embedding" not in kwargs
        mock_repo.create.assert_awaited_once()

    async def test_update_regenerates_embedding_when_title_changes(
        self, mock_repo: AsyncMock, db: AsyncMock, sample_book: Book
    ) -> None:
        sample_book.title = "New Title"
        mock_repo.update.return_value = sample_book
        embedding_gen = AsyncMock(return_value=b"NEW")
        service = BookService(repo=mock_repo, embedding_generator=embedding_gen)

        await service.update(db, 1, title="New Title")

        embedding_gen.assert_awaited_once()
        assert mock_repo.update.await_count == 2
        second_call_kwargs = mock_repo.update.call_args_list[1].kwargs
        assert second_call_kwargs["embedding"] == b"NEW"
        assert second_call_kwargs["embedding_model"] == "baai/bge-m3"

    async def test_update_skips_embedding_when_unrelated_fields_change(
        self, mock_repo: AsyncMock, db: AsyncMock, sample_book: Book
    ) -> None:
        mock_repo.update.return_value = sample_book
        embedding_gen = AsyncMock()
        service = BookService(repo=mock_repo, embedding_generator=embedding_gen)

        await service.update(db, 1, published_date=date(2000, 1, 1))

        embedding_gen.assert_not_awaited()
        assert mock_repo.update.await_count == 1

    async def test_update_succeeds_when_embedding_generator_fails(
        self, mock_repo: AsyncMock, db: AsyncMock, sample_book: Book
    ) -> None:
        mock_repo.update.return_value = sample_book
        embedding_gen = AsyncMock(
            side_effect=APIConnectionError(request=httpx.Request("POST", "https://openrouter.ai"))
        )
        service = BookService(repo=mock_repo, embedding_generator=embedding_gen)

        result = await service.update(db, 1, summary="new summary")

        assert result is sample_book
        embedding_gen.assert_awaited_once()


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
