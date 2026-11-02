from sqlalchemy import CheckConstraint, Column, Date, Integer, String
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
