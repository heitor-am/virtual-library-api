import numpy as np

from app.ai.client import get_openrouter_client, openai_retry
from app.config import get_settings


def build_book_text(title: str, author: str, summary: str | None = None) -> str:
    parts = [title, author]
    if summary:
        parts.append(summary)
    return "\n".join(parts)


@openai_retry
async def generate_embedding(text: str) -> bytes:
    settings = get_settings()
    client = get_openrouter_client()

    response = await client.embeddings.create(
        model=settings.openrouter_embedding_model,
        input=text,
    )
    vector = np.array(response.data[0].embedding, dtype=np.float32)
    return vector.tobytes()


def deserialize_embedding(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def bulk_cosine(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = float(np.linalg.norm(query))
    if query_norm == 0.0 or matrix.shape[0] == 0:
        return np.zeros(matrix.shape[0])

    matrix_norms = np.linalg.norm(matrix, axis=1)
    denominators = np.maximum(matrix_norms * query_norm, 1e-10)
    scores: np.ndarray = (matrix @ query) / denominators
    return scores
