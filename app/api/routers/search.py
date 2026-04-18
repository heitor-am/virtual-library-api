import time

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import BookServiceDep, DbDep
from app.schemas.book import BookRead

router = APIRouter(prefix="/books", tags=["search"])


class SemanticSearchResult(BaseModel):
    book: BookRead
    similarity_score: float


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResult]
    elapsed_ms: float


@router.get(
    "/search/semantic",
    response_model=SemanticSearchResponse,
    summary="Semantic search over book embeddings",
    description=(
        "Ranks all indexed books by cosine similarity to the query. "
        "Skips books without embeddings (created while AI features were off)."
    ),
)
async def semantic_search(
    db: DbDep,
    service: BookServiceDep,
    q: str = Query(..., min_length=1, description="Free-text query"),
    top_k: int = Query(5, ge=1, le=20),
    min_score: float = Query(0.0, ge=-1.0, le=1.0),
) -> SemanticSearchResponse:
    start = time.perf_counter()
    pairs = await service.semantic_search(db, q, top_k=top_k, min_score=min_score)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return SemanticSearchResponse(
        query=q,
        results=[
            SemanticSearchResult(
                book=BookRead.model_validate(book),
                similarity_score=round(score, 4),
            )
            for book, score in pairs
        ],
        elapsed_ms=round(elapsed_ms, 2),
    )
