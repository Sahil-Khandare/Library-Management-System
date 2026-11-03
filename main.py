from contextlib import asynccontextmanager
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import or_, update
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from schemas import BookCreate, BookResponse, BookUpdate
from fastapi.security import OAuth2PasswordRequestForm
from schemas import UserCreate, UserResponse
from models import Book, User, BorrowRecord
from auth import get_current_user
from datetime import datetime

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_admin_user
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Library Management API",
    version="1.1.0",
    lifespan=lifespan,
)


def _get_book_or_404(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book



@app.post("/books/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
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
def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
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
def delete_book(book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    db.delete(db_book)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/books/{book_id}/borrow")
def borrow_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    if book.available_copies <= 0:
        raise HTTPException(
            status_code=400,
            detail="No copies available"
        )

    book.available_copies -= 1

    borrow_record = BorrowRecord(
        user_id=current_user.id,
        book_id=book_id
    )

    db.add(borrow_record)
    db.commit()
    db.refresh(book)

    return {
        "message": "Book borrowed successfully",
        "book": book,
        "borrow_record": borrow_record
    }

@app.post("/books/{book_id}/return")
def return_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    borrow_record = db.query(BorrowRecord).filter(
        BorrowRecord.book_id == book_id,
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.returned_at.is_(None)
    ).first()

    if not borrow_record:
        raise HTTPException(
            status_code=404,
            detail="No active borrowing record found for this book"
        )

    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    borrow_record.returned_at = datetime.now()

    book.available_copies += 1

    db.commit()
    db.refresh(book)

    return {
        "message": "Book returned successfully",
        "book": book,
        "borrow_record": borrow_record
    }

@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_username = db.query(User).filter(
        User.username == user.username
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already registered"
        )

    existing_email = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post("/auth/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    print("Login username:", form_data.username)

    user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    print("User found:", user is not None)

    if user:
        print(
            "Password valid:",
            verify_password(
                form_data.password,
                user.hashed_password
            )
        )

    if not user or not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/auth/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
