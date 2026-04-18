from datetime import date

from app.models.book import Book, SummarySource


def test_book_model_defaults() -> None:
    book = Book(
        title="O Hobbit",
        author="J.R.R. Tolkien",
        published_date=date(1937, 9, 21),
    )
    assert book.title == "O Hobbit"
    assert book.author == "J.R.R. Tolkien"
    assert book.published_date == date(1937, 9, 21)
    assert book.summary is None
    assert book.embedding is None


def test_book_repr_is_informative() -> None:
    book = Book(
        id=42,
        title="1984",
        author="George Orwell",
        published_date=date(1949, 6, 8),
    )
    rendered = repr(book)
    assert "42" in rendered
    assert "1984" in rendered
    assert "George Orwell" in rendered


def test_summary_source_enum_values() -> None:
    assert SummarySource.USER.value == "user"
    assert SummarySource.AI.value == "ai"
    assert str(SummarySource.USER) == "user"
