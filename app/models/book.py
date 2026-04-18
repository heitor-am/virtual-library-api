from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class SummarySource(StrEnum):
    USER = "user"
    AI = "ai"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    published_date: Mapped[date] = mapped_column(nullable=False)
    summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    summary_source: Mapped[SummarySource] = mapped_column(
        SAEnum(SummarySource, name="summary_source"),
        nullable=False,
        default=SummarySource.USER,
        server_default=SummarySource.USER.value,
    )

    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title!r} author={self.author!r}>"
