from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

def _check_copies(available: int | None, total: int | None) -> None:
    if available is not None and total is not None and available > total:
        raise ValueError("Available copies cannot be greater than total copies")


def _check_not_future(value: date | None) -> date | None:
    if value is not None and value > date.today():
        raise ValueError("Published date cannot be in the future")
    return value


class BookCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=100)
    genre: str = Field(min_length=1, max_length=50)
    published_date: date
    total_copies: int = Field(ge=0)
    available_copies: int = Field(ge=0)

    @field_validator("published_date")
    @classmethod
    def published_date_not_future(cls, v):
        return _check_not_future(v)

    @model_validator(mode="after")
    def copies_consistent(self):
        _check_copies(self.available_copies, self.total_copies)
        return self


class BookUpdate(BaseModel):

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    genre: str | None = Field(default=None, min_length=1, max_length=50)
    published_date: date | None = None
    total_copies: int | None = Field(default=None, ge=0)
    available_copies: int | None = Field(default=None, ge=0)

    @field_validator("published_date")
    @classmethod
    def published_date_not_future(cls, v):
        return _check_not_future(v)

    @model_validator(mode="after")
    def copies_consistent(self):
        _check_copies(self.available_copies, self.total_copies)
        return self

class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    genre: str
    published_date: date
    total_copies: int
    available_copies: int

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str

class BorrowRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book_id: int
    borrowed_at: datetime
    returned_at: datetime | None
