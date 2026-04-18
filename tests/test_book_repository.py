from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import SummarySource
from app.repositories.book import BookRepository


@pytest.fixture
def repo() -> BookRepository:
    return BookRepository()


async def _seed(repo: BookRepository, db: AsyncSession) -> None:
    await repo.create(
        db,
        title="O Hobbit",
        author="J.R.R. Tolkien",
        published_date=date(1937, 9, 21),
        summary="Aventura na Terra Média",
    )
    await repo.create(
        db,
        title="The Lord of the Rings",
        author="J.R.R. Tolkien",
        published_date=date(1954, 7, 29),
    )
    await repo.create(
        db,
        title="1984",
        author="George Orwell",
        published_date=date(1949, 6, 8),
    )
    await repo.create(
        db,
        title="Dom Casmurro",
        author="Machado de Assis",
        published_date=date(1899, 1, 1),
    )


class TestCreate:
    async def test_create_returns_book_with_id(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        book = await repo.create(
            db_session,
            title="1984",
            author="George Orwell",
            published_date=date(1949, 6, 8),
        )
        assert book.id is not None
        assert book.title == "1984"
        assert book.summary_source == SummarySource.USER

    async def test_create_sets_timestamps(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        book = await repo.create(
            db_session,
            title="1984",
            author="Orwell",
            published_date=date(1949, 6, 8),
        )
        assert book.created_at is not None
        assert book.updated_at is not None


class TestGet:
    async def test_get_returns_book_by_id(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        created = await repo.create(
            db_session,
            title="1984",
            author="Orwell",
            published_date=date(1949, 6, 8),
        )
        found = await repo.get(db_session, created.id)
        assert found is not None
        assert found.id == created.id

    async def test_get_returns_none_for_missing_id(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        assert await repo.get(db_session, 999) is None


class TestList:
    async def test_list_returns_all_unfiltered(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        await _seed(repo, db_session)
        items, total = await repo.list(db_session)
        assert total == 4
        assert len(items) == 4

    async def test_list_filter_by_title_case_insensitive(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        await _seed(repo, db_session)
        items, total = await repo.list(db_session, title="hobbit")
        assert total == 1
        assert items[0].title == "O Hobbit"

    async def test_list_filter_by_author_partial(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        await _seed(repo, db_session)
        items, total = await repo.list(db_session, author="tolkien")
        assert total == 2
        assert all("Tolkien" in b.author for b in items)

    async def test_list_both_filters_combined(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        await _seed(repo, db_session)
        items, total = await repo.list(db_session, title="lord", author="tolkien")
        assert total == 1
        assert items[0].title == "The Lord of the Rings"

    async def test_list_pagination_skip_and_limit(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        await _seed(repo, db_session)
        items, total = await repo.list(db_session, skip=2, limit=2)
        assert total == 4
        assert len(items) == 2

    async def test_list_ordering_by_title_asc(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        await _seed(repo, db_session)
        items, _ = await repo.list(db_session, sort_by="title", order="asc")
        titles = [b.title for b in items]
        assert titles == sorted(titles)

    async def test_list_ordering_by_published_date_desc(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        await _seed(repo, db_session)
        items, _ = await repo.list(db_session, sort_by="published_date", order="desc")
        dates = [b.published_date for b in items]
        assert dates == sorted(dates, reverse=True)


class TestUpdate:
    async def test_update_modifies_fields(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        created = await repo.create(
            db_session,
            title="1984",
            author="Orwell",
            published_date=date(1949, 6, 8),
        )
        updated = await repo.update(db_session, created.id, summary="Dystopia")
        assert updated is not None
        assert updated.summary == "Dystopia"
        assert updated.title == "1984"

    async def test_update_partial_leaves_other_fields(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        created = await repo.create(
            db_session,
            title="Original",
            author="Author",
            published_date=date(2000, 1, 1),
            summary="original summary",
        )
        updated = await repo.update(db_session, created.id, title="New Title")
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.summary == "original summary"

    async def test_update_returns_none_for_missing(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        result = await repo.update(db_session, 999, title="ghost")
        assert result is None


class TestDelete:
    async def test_delete_removes_book(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        created = await repo.create(
            db_session,
            title="1984",
            author="Orwell",
            published_date=date(1949, 6, 8),
        )
        result = await repo.delete(db_session, created.id)
        assert result is True
        assert await repo.get(db_session, created.id) is None

    async def test_delete_returns_false_for_missing(
        self, repo: BookRepository, db_session: AsyncSession
    ) -> None:
        assert await repo.delete(db_session, 999) is False
