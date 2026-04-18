from collections.abc import AsyncGenerator
from datetime import date
from unittest.mock import AsyncMock

import httpx
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from openai import APIConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_book_service
from app.config import get_settings
from app.core.exceptions import LLMUnavailableError
from app.database import get_db
from app.main import app
from app.repositories.book import BookRepository
from app.services.book import BookService


def _vec(*values: float) -> bytes:
    return np.array(values, dtype=np.float32).tobytes()


async def _seed_with_vectors(
    db: AsyncSession,
    repo: BookRepository,
    entries: list[tuple[str, bytes]],
) -> None:
    for title, vector in entries:
        await repo.create(
            db,
            title=title,
            author="Author",
            published_date=date(2000, 1, 1),
            embedding=vector,
            embedding_model="test-model",
        )


class TestSemanticSearchService:
    @pytest.fixture(autouse=True)
    def _ai_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("AI_FEATURES_ENABLED", "true")
        get_settings.cache_clear()

    async def test_returns_empty_when_no_books(self, db_session: AsyncSession) -> None:
        embedding_gen = AsyncMock()
        service = BookService(embedding_generator=embedding_gen)

        results = await service.semantic_search(db_session, "anything")

        assert results == []
        embedding_gen.assert_not_awaited()  # no wasted LLM call

    async def test_returns_most_similar_first(self, db_session: AsyncSession) -> None:
        repo = BookRepository()
        await _seed_with_vectors(
            db_session,
            repo,
            [
                ("A", _vec(1.0, 0.0, 0.0)),
                ("B", _vec(0.0, 1.0, 0.0)),
                ("C", _vec(0.0, 0.0, 1.0)),
            ],
        )

        # Query vector closest to A's direction
        embedding_gen = AsyncMock(return_value=_vec(0.9, 0.1, 0.0))
        service = BookService(repo=repo, embedding_generator=embedding_gen)

        results = await service.semantic_search(db_session, "about A", top_k=3)

        assert len(results) == 3
        assert results[0][0].title == "A"
        assert results[0][1] > results[1][1]
        assert results[1][1] >= results[2][1]

    async def test_top_k_limits_results(self, db_session: AsyncSession) -> None:
        repo = BookRepository()
        await _seed_with_vectors(
            db_session,
            repo,
            [
                ("A", _vec(1.0, 0.0, 0.0)),
                ("B", _vec(0.9, 0.1, 0.0)),
                ("C", _vec(0.8, 0.2, 0.0)),
                ("D", _vec(0.0, 0.0, 1.0)),
            ],
        )
        embedding_gen = AsyncMock(return_value=_vec(1.0, 0.0, 0.0))
        service = BookService(repo=repo, embedding_generator=embedding_gen)

        results = await service.semantic_search(db_session, "query", top_k=2)

        assert len(results) == 2

    async def test_min_score_filters_low_similarity(self, db_session: AsyncSession) -> None:
        repo = BookRepository()
        await _seed_with_vectors(
            db_session,
            repo,
            [
                ("close", _vec(1.0, 0.0, 0.0)),
                ("far", _vec(0.0, 0.0, 1.0)),
            ],
        )
        embedding_gen = AsyncMock(return_value=_vec(1.0, 0.0, 0.0))
        service = BookService(repo=repo, embedding_generator=embedding_gen)

        results = await service.semantic_search(db_session, "q", min_score=0.5)

        assert len(results) == 1
        assert results[0][0].title == "close"

    async def test_raises_llm_unavailable_on_embedding_failure(
        self, db_session: AsyncSession
    ) -> None:
        repo = BookRepository()
        await _seed_with_vectors(db_session, repo, [("A", _vec(1.0, 0.0))])

        embedding_gen = AsyncMock(
            side_effect=APIConnectionError(request=httpx.Request("POST", "https://openrouter.ai"))
        )
        service = BookService(repo=repo, embedding_generator=embedding_gen)

        with pytest.raises(LLMUnavailableError):
            await service.semantic_search(db_session, "q")


class TestSemanticSearchEndpoint:
    @pytest.fixture
    async def ai_client(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> AsyncGenerator[tuple[AsyncClient, AsyncMock], None]:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("AI_FEATURES_ENABLED", "true")
        get_settings.cache_clear()

        repo = BookRepository()
        await _seed_with_vectors(
            db_session,
            repo,
            [
                ("Aventura", _vec(1.0, 0.0, 0.0)),
                ("Romance", _vec(0.0, 1.0, 0.0)),
                ("Ficção Científica", _vec(0.0, 0.0, 1.0)),
            ],
        )

        fake_embedder = AsyncMock(return_value=_vec(0.95, 0.05, 0.0))
        test_service = BookService(repo=repo, embedding_generator=fake_embedder)

        async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_book_service] = lambda: test_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, fake_embedder

        app.dependency_overrides.clear()

    async def test_endpoint_returns_ranked_results(
        self, ai_client: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, _ = ai_client
        response = await client.get("/books/search/semantic", params={"q": "heroi lutando"})
        assert response.status_code == 200

        body = response.json()
        assert body["query"] == "heroi lutando"
        assert "elapsed_ms" in body
        assert body["elapsed_ms"] >= 0
        assert len(body["results"]) == 3

        first = body["results"][0]
        assert first["book"]["title"] == "Aventura"
        assert first["similarity_score"] > body["results"][1]["similarity_score"]

    async def test_endpoint_respects_top_k(self, ai_client: tuple[AsyncClient, AsyncMock]) -> None:
        client, _ = ai_client
        response = await client.get("/books/search/semantic", params={"q": "teste", "top_k": 1})
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    async def test_endpoint_requires_non_empty_query(
        self, ai_client: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, _ = ai_client
        response = await client.get("/books/search/semantic", params={"q": ""})
        assert response.status_code == 422

    async def test_endpoint_enforces_top_k_upper_bound(
        self, ai_client: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, _ = ai_client
        response = await client.get("/books/search/semantic", params={"q": "x", "top_k": 99})
        assert response.status_code == 422

    async def test_llm_failure_returns_503_problem_details(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        get_settings.cache_clear()

        repo = BookRepository()
        await _seed_with_vectors(db_session, repo, [("A", _vec(1.0, 0.0))])

        failing = AsyncMock(
            side_effect=APIConnectionError(request=httpx.Request("POST", "https://openrouter.ai"))
        )
        test_service = BookService(repo=repo, embedding_generator=failing)

        async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_book_service] = lambda: test_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/books/search/semantic", params={"q": "fail"})

        app.dependency_overrides.clear()

        assert response.status_code == 503
        assert response.headers["content-type"].startswith("application/problem+json")
        body = response.json()
        assert body["code"] == "LLM_UNAVAILABLE"
