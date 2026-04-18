from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from app.ai.embeddings import (
    build_book_text,
    bulk_cosine,
    cosine_similarity,
    deserialize_embedding,
    generate_embedding,
)
from app.config import get_settings


@pytest.fixture(autouse=True)
def _openrouter_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_EMBEDDING_MODEL", "baai/bge-m3")
    get_settings.cache_clear()


def _make_mock_client(embedding: list[float]) -> MagicMock:
    datum = MagicMock()
    datum.embedding = embedding
    response = MagicMock()
    response.data = [datum]

    client = MagicMock()
    client.embeddings.create = AsyncMock(return_value=response)
    return client


class TestBuildBookText:
    def test_with_summary(self) -> None:
        text = build_book_text("O Hobbit", "Tolkien", "Aventura na Terra Média")
        assert "O Hobbit" in text
        assert "Tolkien" in text
        assert "Aventura" in text

    def test_without_summary(self) -> None:
        text = build_book_text("O Hobbit", "Tolkien")
        assert "O Hobbit" in text
        assert "Tolkien" in text
        assert text.count("\n") == 1

    def test_empty_summary_is_skipped(self) -> None:
        text = build_book_text("T", "A", "")
        assert text.count("\n") == 1


class TestGenerateEmbedding:
    async def test_returns_serialized_float32_bytes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        vector = [0.1, 0.2, 0.3, 0.4]
        mock_client = _make_mock_client(vector)
        monkeypatch.setattr("app.ai.embeddings.get_openrouter_client", lambda: mock_client)

        blob = await generate_embedding("hello")

        restored = np.frombuffer(blob, dtype=np.float32)
        np.testing.assert_allclose(restored, vector, atol=1e-6)

    async def test_sends_configured_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_client = _make_mock_client([0.0, 0.0])
        monkeypatch.setattr("app.ai.embeddings.get_openrouter_client", lambda: mock_client)

        await generate_embedding("hello")

        kwargs = mock_client.embeddings.create.call_args.kwargs
        assert kwargs["model"] == "baai/bge-m3"
        assert kwargs["input"] == "hello"


class TestDeserializeEmbedding:
    def test_roundtrip_preserves_values(self) -> None:
        original = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        blob = original.tobytes()
        restored = deserialize_embedding(blob)
        np.testing.assert_array_equal(restored, original)

    def test_dtype_is_float32(self) -> None:
        blob = np.array([1.0, 2.0], dtype=np.float32).tobytes()
        assert deserialize_embedding(blob).dtype == np.float32


class TestCosineSimilarity:
    def test_identical_vectors_yield_one(self) -> None:
        v = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_opposite_vectors_yield_minus_one(self) -> None:
        a = np.array([1.0, 0.0], dtype=np.float32)
        b = np.array([-1.0, 0.0], dtype=np.float32)
        assert cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_orthogonal_vectors_yield_zero(self) -> None:
        a = np.array([1.0, 0.0], dtype=np.float32)
        b = np.array([0.0, 1.0], dtype=np.float32)
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_zero_vector_yields_zero(self) -> None:
        a = np.array([0.0, 0.0], dtype=np.float32)
        b = np.array([1.0, 2.0], dtype=np.float32)
        assert cosine_similarity(a, b) == 0.0
        assert cosine_similarity(b, a) == 0.0


class TestBulkCosine:
    def test_matches_pairwise_cosine(self) -> None:
        query = np.array([1.0, 0.0], dtype=np.float32)
        matrix = np.array(
            [
                [1.0, 0.0],  # identical
                [-1.0, 0.0],  # opposite
                [0.0, 1.0],  # orthogonal
                [0.5, 0.5],  # 45 degrees
            ],
            dtype=np.float32,
        )
        scores = bulk_cosine(query, matrix)
        assert scores[0] == pytest.approx(1.0)
        assert scores[1] == pytest.approx(-1.0)
        assert scores[2] == pytest.approx(0.0)
        assert scores[3] == pytest.approx(0.7071, abs=1e-3)

    def test_zero_query_returns_zeros(self) -> None:
        query = np.array([0.0, 0.0], dtype=np.float32)
        matrix = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        scores = bulk_cosine(query, matrix)
        assert np.all(scores == 0.0)

    def test_empty_matrix_returns_empty(self) -> None:
        query = np.array([1.0, 0.0], dtype=np.float32)
        matrix = np.zeros((0, 2), dtype=np.float32)
        scores = bulk_cosine(query, matrix)
        assert scores.shape == (0,)
