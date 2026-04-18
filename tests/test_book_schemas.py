from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.models.book import Book, SummarySource
from app.schemas.book import BookCreate, BookList, BookRead, BookUpdate


class TestBookCreate:
    def test_valid_payload(self) -> None:
        payload = BookCreate(
            title="O Hobbit",
            author="J.R.R. Tolkien",
            published_date=date(1937, 9, 21),
            summary="Bilbo embarca em uma aventura",
        )
        assert payload.title == "O Hobbit"
        assert payload.summary == "Bilbo embarca em uma aventura"

    def test_summary_is_optional(self) -> None:
        payload = BookCreate(
            title="1984",
            author="George Orwell",
            published_date=date(1949, 6, 8),
        )
        assert payload.summary is None

    def test_missing_title_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc:
            BookCreate.model_validate({"author": "Tolkien", "published_date": "1937-09-21"})
        assert "title" in str(exc.value)

    def test_empty_title_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BookCreate(title="", author="Tolkien", published_date=date(1937, 9, 21))

    def test_title_too_long_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BookCreate(
                title="a" * 501,
                author="Tolkien",
                published_date=date(1937, 9, 21),
            )

    def test_invalid_date_format_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BookCreate.model_validate(
                {
                    "title": "O Hobbit",
                    "author": "Tolkien",
                    "published_date": "not-a-date",
                }
            )


class TestBookUpdate:
    def test_all_fields_optional(self) -> None:
        payload = BookUpdate()
        assert payload.title is None
        assert payload.author is None
        assert payload.published_date is None
        assert payload.summary is None

    def test_partial_update(self) -> None:
        payload = BookUpdate(summary="new summary")
        assert payload.summary == "new summary"
        assert payload.title is None

    def test_empty_string_title_is_still_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BookUpdate(title="")


class TestBookRead:
    def test_from_orm_model(self) -> None:
        book = Book(
            id=42,
            title="O Hobbit",
            author="Tolkien",
            published_date=date(1937, 9, 21),
            summary=None,
            summary_source=SummarySource.USER,
            created_at=datetime(2026, 4, 18, 12, 0, 0),
            updated_at=datetime(2026, 4, 18, 12, 0, 0),
        )
        read = BookRead.model_validate(book)
        assert read.id == 42
        assert read.summary_source == SummarySource.USER
        assert read.title == "O Hobbit"


class TestBookList:
    def test_envelope_structure(self) -> None:
        envelope = BookList(items=[], total=0, skip=0, limit=20)
        assert envelope.items == []
        assert envelope.total == 0
        assert envelope.skip == 0
        assert envelope.limit == 20


class TestJsonSchema:
    def test_book_create_generates_valid_schema(self) -> None:
        schema = BookCreate.model_json_schema()
        assert schema["type"] == "object"
        assert "title" in schema["properties"]
        assert "author" in schema["properties"]
        assert "published_date" in schema["properties"]
        assert set(schema["required"]) == {"title", "author", "published_date"}

    def test_book_read_includes_all_output_fields(self) -> None:
        schema = BookRead.model_json_schema()
        required = set(schema["required"])
        assert {
            "id",
            "title",
            "author",
            "published_date",
            "summary_source",
            "created_at",
            "updated_at",
        }.issubset(required)
