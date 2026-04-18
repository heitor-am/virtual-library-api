from fastapi import APIRouter, Query, status

from app.api.deps import BookServiceDep, DbDep
from app.repositories.book import SortField, SortOrder
from app.schemas.book import BookCreate, BookList, BookRead, BookUpdate

router = APIRouter(prefix="/books", tags=["books"])


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book",
)
async def create_book(payload: BookCreate, db: DbDep, service: BookServiceDep) -> BookRead:
    book = await service.create(db, **payload.model_dump())
    return BookRead.model_validate(book)


@router.get(
    "",
    response_model=BookList,
    summary="List books with optional filters, pagination and ordering",
)
async def list_books(
    db: DbDep,
    service: BookServiceDep,
    title: str | None = Query(None, description="Case-insensitive partial match on title"),
    author: str | None = Query(None, description="Case-insensitive partial match on author"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: SortField = "created_at",
    order: SortOrder = "desc",
) -> BookList:
    items, total = await service.list(
        db,
        title=title,
        author=author,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )
    return BookList(
        items=[BookRead.model_validate(b) for b in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{book_id}",
    response_model=BookRead,
    summary="Get a book by ID",
    responses={404: {"description": "Book not found"}},
)
async def get_book(book_id: int, db: DbDep, service: BookServiceDep) -> BookRead:
    book = await service.get(db, book_id)
    return BookRead.model_validate(book)


@router.put(
    "/{book_id}",
    response_model=BookRead,
    summary="Update a book (partial)",
    responses={404: {"description": "Book not found"}},
)
async def update_book(
    book_id: int, payload: BookUpdate, db: DbDep, service: BookServiceDep
) -> BookRead:
    data = payload.model_dump(exclude_unset=True)
    book = await service.update(db, book_id, **data)
    return BookRead.model_validate(book)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    responses={404: {"description": "Book not found"}},
)
async def delete_book(book_id: int, db: DbDep, service: BookServiceDep) -> None:
    await service.delete(db, book_id)
