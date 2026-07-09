    import uvicorn
    from fastapi import FastAPI, Depends, HTTPException
    from sqlalchemy.orm import Session
    from database import Base, engine, get_db
    from models import Book
    from schemas import BookCreate, BookUpdate, BookResponse

    app = FastAPI()

    Base.metadata.create_all(bind=engine)

    @app.post("/books/", response_model=BookResponse, status_code=201)
    def create_book(book: BookCreate, db: Session = Depends(get_db)):
        new_book = Book(
            title=book.title,
            author=book.author,
            genre=book.genre,
            published_date=book.published_date,
            total_copies=book.total_copies,
            available_copies=book.available_copies
        )
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        return new_book

    @app.get("/books/", response_model=list[BookResponse])
    def get_books(db: Session = Depends(get_db)):
        books = db.query(Book).all()
        return books

    @app.get("/books/{book_id}", response_model=BookResponse)
    def get_book(book_id: int, db: Session = Depends(get_db)):
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book

    @app.delete("/books/{book_id}", response_model=BookResponse)
    def delete_book(book_id: int, db: Session = Depends(get_db)):
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        db.delete(book)
        db.commit()
        return book

    @app.patch("/books/{book_id}", response_model=BookResponse)
    def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db)):
        db_book = db.query(Book).filter(Book.id == book_id).first()
        if not db_book:
            raise HTTPException(status_code=404, detail="Book not found")
        for key, value in book.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(db_book, key, value)
        if db_book.available_copies > db_book.total_copies:
            raise HTTPException(
                status_code=400,
                detail="Available copies cannot be greater than total copies"
            )     
        db.commit()
        db.refresh(db_book)
        return db_book

    if __name__ == "__main__":
        uvicorn.run(app, host="127.0.0.1", port=8000)
