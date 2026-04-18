from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

    @model_validator(mode="after")
    def reject_null_on_not_null_columns(self) -> Self:
        # These columns are NOT NULL at the DB level. Accepting `null` here
        # would either fail at commit time with a constraint error or silently
        # confuse clients expecting "omit field = skip update".
        for field in ("title", "author", "published_date"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' cannot be null; omit the field to skip updating it")
        return self


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
