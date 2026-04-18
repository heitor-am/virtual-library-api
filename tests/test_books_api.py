from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_book_service
from app.config import get_settings
from app.database import get_db
from app.main import app
from app.services.book import BookService

BOOK_HOBBIT = {
    "title": "O Hobbit",
    "author": "J.R.R. Tolkien",
    "published_date": "1937-09-21",
    "summary": "Aventura na Terra Média",
}

BOOK_1984 = {
    "title": "1984",
    "author": "George Orwell",
    "published_date": "1949-06-08",
}


class TestCreateBook:
    async def test_creates_book_with_summary(self, client: AsyncClient) -> None:
        response = await client.post("/books", json=BOOK_HOBBIT)
        assert response.status_code == 201

        body = response.json()
        assert body["id"] is not None
        assert body["title"] == "O Hobbit"
        assert body["summary"] == "Aventura na Terra Média"
        assert body["summary_source"] == "user"

    async def test_creates_book_without_summary(self, client: AsyncClient) -> None:
        response = await client.post("/books", json=BOOK_1984)
        assert response.status_code == 201
        assert response.json()["summary"] is None

    async def test_missing_title_returns_422_problem_details(self, client: AsyncClient) -> None:
        response = await client.post(
            "/books",
            json={"author": "Tolkien", "published_date": "1937-09-21"},
        )
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/problem+json")

        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert "title" in body["detail"]
        assert body["status"] == 422


class TestListBooks:
    async def test_returns_empty_list_initially(self, client: AsyncClient) -> None:
        response = await client.get("/books")
        assert response.status_code == 200
        body = response.json()
        assert body == {"items": [], "total": 0, "skip": 0, "limit": 20}

    async def test_returns_created_books(self, client: AsyncClient) -> None:
        await client.post("/books", json=BOOK_HOBBIT)
        await client.post("/books", json=BOOK_1984)

        response = await client.get("/books")
        assert response.status_code == 200

        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    async def test_filters_by_title_case_insensitive(self, client: AsyncClient) -> None:
        await client.post("/books", json=BOOK_HOBBIT)
        await client.post("/books", json=BOOK_1984)

        response = await client.get("/books", params={"title": "hobbit"})
        assert response.status_code == 200

        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["title"] == "O Hobbit"

    async def test_filters_by_author_partial(self, client: AsyncClient) -> None:
        await client.post("/books", json=BOOK_HOBBIT)
        await client.post("/books", json=BOOK_1984)

        response = await client.get("/books", params={"author": "orwell"})
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["author"] == "George Orwell"

    async def test_pagination(self, client: AsyncClient) -> None:
        for i in range(5):
            await client.post(
                "/books",
                json={
                    "title": f"Book {i}",
                    "author": "Author",
                    "published_date": "2000-01-01",
                },
            )

        response = await client.get("/books", params={"skip": 2, "limit": 2})
        body = response.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2
        assert body["skip"] == 2
        assert body["limit"] == 2

    async def test_limit_upper_bound_enforced(self, client: AsyncClient) -> None:
        response = await client.get("/books", params={"limit": 999})
        assert response.status_code == 422


class TestGetBook:
    async def test_returns_book_by_id(self, client: AsyncClient) -> None:
        created = (await client.post("/books", json=BOOK_HOBBIT)).json()

        response = await client.get(f"/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["title"] == "O Hobbit"

    async def test_missing_id_returns_404_problem_details(self, client: AsyncClient) -> None:
        response = await client.get("/books/999")
        assert response.status_code == 404
        assert response.headers["content-type"].startswith("application/problem+json")

        body = response.json()
        assert body["code"] == "BOOK_NOT_FOUND"
        assert body["status"] == 404
        assert "999" in body["detail"]


class TestUpdateBook:
    async def test_updates_book(self, client: AsyncClient) -> None:
        created = (await client.post("/books", json=BOOK_HOBBIT)).json()

        response = await client.put(
            f"/books/{created['id']}",
            json={"summary": "Updated summary"},
        )
        assert response.status_code == 200
        assert response.json()["summary"] == "Updated summary"
        assert response.json()["title"] == "O Hobbit"

    async def test_missing_id_returns_404_problem_details(self, client: AsyncClient) -> None:
        response = await client.put("/books/999", json={"title": "Ghost"})
        assert response.status_code == 404

        body = response.json()
        assert body["code"] == "BOOK_NOT_FOUND"

    async def test_explicit_null_on_required_field_returns_422_problem_details(
        self, client: AsyncClient
    ) -> None:
        created = (await client.post("/books", json=BOOK_HOBBIT)).json()

        response = await client.put(f"/books/{created['id']}", json={"title": None})
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/problem+json")

        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert "title" in body["detail"]
        assert "null" in body["detail"].lower()

    async def test_explicit_null_on_summary_is_accepted(self, client: AsyncClient) -> None:
        created = (await client.post("/books", json=BOOK_HOBBIT)).json()

        response = await client.put(f"/books/{created['id']}", json={"summary": None})
        assert response.status_code == 200
        assert response.json()["summary"] is None


class TestDeleteBook:
    async def test_deletes_book(self, client: AsyncClient) -> None:
        created = (await client.post("/books", json=BOOK_HOBBIT)).json()

        response = await client.delete(f"/books/{created['id']}")
        assert response.status_code == 204

        get_response = await client.get(f"/books/{created['id']}")
        assert get_response.status_code == 404

    async def test_missing_id_returns_404_problem_details(self, client: AsyncClient) -> None:
        response = await client.delete("/books/999")
        assert response.status_code == 404

        body = response.json()
        assert body["code"] == "BOOK_NOT_FOUND"


class TestAutoSummaryIntegration:
    """POST /books without summary triggers LLM generation."""

    @pytest.fixture
    async def ai_client(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> AsyncGenerator[tuple[AsyncClient, AsyncMock], None]:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("AI_FEATURES_ENABLED", "true")
        get_settings.cache_clear()

        fake_generator = AsyncMock(return_value="Generated by AI")
        test_service = BookService(summary_generator=fake_generator)

        async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_book_service] = lambda: test_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, fake_generator

        app.dependency_overrides.clear()

    async def test_post_without_summary_triggers_llm(
        self, ai_client: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, fake_generator = ai_client
        response = await client.post(
            "/books",
            json={
                "title": "O Hobbit",
                "author": "J.R.R. Tolkien",
                "published_date": "1937-09-21",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["summary"] == "Generated by AI"
        assert body["summary_source"] == "ai"
        fake_generator.assert_awaited_once_with("O Hobbit", "J.R.R. Tolkien")

    async def test_post_with_summary_skips_llm(
        self, ai_client: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, fake_generator = ai_client
        response = await client.post("/books", json=BOOK_HOBBIT)
        assert response.status_code == 201
        body = response.json()
        assert body["summary"] == "Aventura na Terra Média"
        assert body["summary_source"] == "user"
        fake_generator.assert_not_awaited()
