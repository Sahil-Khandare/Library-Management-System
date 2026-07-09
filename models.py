from sqlalchemy import Column, Integer, String, Date
from database import Base

class Book(Base):
    __tablename__ = "Books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(30), nullable=False)
    author = Column(String(30), nullable=False)
    genre = Column(String(15), nullable=False)
    published_date = Column(Date, nullable=False)
    total_copies = Column(Integer, nullable=False)
    available_copies = Column(Integer, nullable=False)