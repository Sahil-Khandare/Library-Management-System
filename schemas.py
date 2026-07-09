from datetime import date
from pydantic import BaseModel, ConfigDict, model_validator

class BookCreate(BaseModel):
    title: str
    author: str
    genre: str
    published_date: date
    total_copies: int
    available_copies: int

    @model_validator(mode="after")
    def check_copies(self):
        if self.available_copies is not None and self.total_copies is not None:
            if self.available_copies > self.total_copies:
                raise ValueError("Available copies cannot be greater than total copies")
        return self

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    genre: str
    published_date: date
    total_copies: int
    available_copies: int

    model_config = ConfigDict(from_attributes=True)

class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    genre: str | None = None
    published_date: date | None = None
    total_copies: int | None = None
    available_copies: int | None = None

    @model_validator(mode="after")
    def check_copies(self):
        if self.available_copies is not None and self.total_copies is not None:
            if self.available_copies > self.total_copies:
                raise ValueError("Available copies cannot be greater than total copies")
        return self
