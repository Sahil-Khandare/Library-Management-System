from sqlalchemy import CheckConstraint, Column, Date, DateTime, Integer, String, func, ForeignKey
from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)  
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    genre = Column(String(50), nullable=False)
    published_date = Column(Date, nullable=False)
    total_copies = Column(Integer, nullable=False)
    available_copies = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("total_copies >= 0", name="ck_books_total_copies_non_negative"),
        CheckConstraint("available_copies >= 0", name="ck_books_available_copies_non_negative"),
        CheckConstraint("available_copies <= total_copies", name="ck_books_available_lte_total"),
    )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")

class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    book_id = Column(
        Integer,
        ForeignKey("books.id"),
        nullable=False
    )

    borrowed_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    returned_at = Column(
        DateTime,
        nullable=True
    )
