from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Book
from schemas import BookCreate, BookResponse, BookUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Library Management API",
    description="CRUD, search and borrow/return operations for a library's book catalog.",
    version="1.1.0",
    lifespan=lifespan,
)


def _get_book_or_404(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book



@app.post("/books/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    new_book = Book(**book.model_dump())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@app.get("/books/", response_model=list[BookResponse])
def get_books(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    search: str | None = Query(None, min_length=1, max_length=100,
                               description="Match against title or author"),
    genre: str | None = Query(None, description="Exact genre filter"),
    available_only: bool = Query(False, description="Only books with copies in stock"),
    db: Session = Depends(get_db),
):
    query = db.query(Book)

    if search:
        query = query.filter(
            or_(
                Book.title.contains(search, autoescape=True),
                Book.author.contains(search, autoescape=True),
            )
        )
    if genre:
        query = query.filter(Book.genre == genre)
    if available_only:
        query = query.filter(Book.available_copies > 0)

    return query.order_by(Book.id).offset(skip).limit(limit).all()


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    return _get_book_or_404(db, book_id)



@app.patch("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db)):
    db_book = _get_book_or_404(db, book_id)

    data = book.model_dump(exclude_unset=True, exclude_none=True)
    if not data:
        raise HTTPException(status_code=422, detail="No fields provided to update")

    new_total = data.get("total_copies", db_book.total_copies)
    new_available = data.get("available_copies", db_book.available_copies)
    if new_available > new_total:
        raise HTTPException(
            status_code=422,
            detail="Available copies cannot be greater than total copies",
        )

    for key, value in data.items():
        setattr(db_book, key, value)

    db.commit()
    db.refresh(db_book)
    return db_book



@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = _get_book_or_404(db, book_id)
    db.delete(db_book)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/books/{book_id}/borrow", response_model=BookResponse)
def borrow_book(book_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        update(Book)
        .where(Book.id == book_id, Book.available_copies > 0)
        .values(available_copies=Book.available_copies - 1)
    )
    if result.rowcount == 0:
        _get_book_or_404(db, book_id)  
        raise HTTPException(status_code=409, detail="No copies available to borrow")
    db.commit()
    return db.get(Book, book_id)


@app.post("/books/{book_id}/return", response_model=BookResponse)
def return_book(book_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        update(Book)
        .where(Book.id == book_id, Book.available_copies < Book.total_copies)
        .values(available_copies=Book.available_copies + 1)
    )
    if result.rowcount == 0:
        _get_book_or_404(db, book_id)
        raise HTTPException(status_code=409, detail="All copies are already in the library")
    db.commit()
    return db.get(Book, book_id)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
