from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.book import SummarySource


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    author: str = Field(min_length=1, max_length=200)
    published_date: date
    summary: str | None = Field(default=None, max_length=2000)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    author: str | None = Field(default=None, min_length=1, max_length=200)
    published_date: date | None = None
    summary: str | None = Field(default=None, max_length=2000)


class BookRead(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    summary_source: SummarySource
    created_at: datetime
    updated_at: datetime


class BookList(BaseModel):
    items: list[BookRead]
    total: int
    skip: int
    limit: int
