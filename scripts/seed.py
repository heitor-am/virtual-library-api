import asyncio
from datetime import date

from sqlalchemy import select

from app.database import SessionLocal
from app.models.book import Book
from app.services.book import book_service

SEEDS: list[tuple[str, str, date]] = [
    ("O Hobbit", "J.R.R. Tolkien", date(1937, 9, 21)),
    ("O Senhor dos Anéis", "J.R.R. Tolkien", date(1954, 7, 29)),
    ("1984", "George Orwell", date(1949, 6, 8)),
    ("Admirável Mundo Novo", "Aldous Huxley", date(1932, 1, 1)),
    ("Dom Casmurro", "Machado de Assis", date(1899, 1, 1)),
    ("Memórias Póstumas de Brás Cubas", "Machado de Assis", date(1881, 1, 1)),
    ("O Cortiço", "Aluísio Azevedo", date(1890, 1, 1)),
    ("Fundação", "Isaac Asimov", date(1951, 5, 1)),
    ("Duna", "Frank Herbert", date(1965, 8, 1)),
    ("O Guia do Mochileiro das Galáxias", "Douglas Adams", date(1979, 10, 12)),
    ("Cem Anos de Solidão", "Gabriel García Márquez", date(1967, 5, 30)),
    ("O Alquimista", "Paulo Coelho", date(1988, 1, 1)),
    ("Crime e Castigo", "Fiódor Dostoiévski", date(1866, 11, 1)),
    ("Orgulho e Preconceito", "Jane Austen", date(1813, 1, 28)),
    ("O Pequeno Príncipe", "Antoine de Saint-Exupéry", date(1943, 4, 6)),
    ("O Conde de Monte Cristo", "Alexandre Dumas", date(1844, 8, 28)),
    ("A Metamorfose", "Franz Kafka", date(1915, 10, 1)),
    ("Neuromancer", "William Gibson", date(1984, 7, 1)),
]


async def main() -> None:
    created = 0
    skipped = 0

    async with SessionLocal() as db:
        for title, author, published in SEEDS:
            stmt = select(Book).where(Book.title == title, Book.author == author)
            if (await db.execute(stmt)).scalar_one_or_none():
                print(f"  · skip: {title} — {author}")
                skipped += 1
                continue

            print(f"  → creating: {title} — {author}")
            await book_service.create(
                db,
                title=title,
                author=author,
                published_date=published,
            )
            created += 1

    print(f"\nSeeded: {created} created, {skipped} already present")


if __name__ == "__main__":
    asyncio.run(main())
