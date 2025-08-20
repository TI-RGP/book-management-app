from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base

class BookStatus(enum.Enum):
    available = "available"
    borrowed = "borrowed"
    reserved = "reserved"

class ReservationStatus(enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"

class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    parent_id = Column(Integer, ForeignKey("genres.id"), nullable=True)
    level = Column(Integer, default=1, nullable=False)  # 1=大分類, 2=中分類, 3=小分類
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    parent = relationship("Genre", remote_side=[id], backref="children")
    books = relationship("Book", back_populates="genre_obj")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    genre_id = Column(Integer, ForeignKey("genres.id"), nullable=True)
    genre = Column(String, nullable=True, index=True)  # Keep for backward compatibility
    isbn = Column(String, nullable=True, index=True)
    publisher = Column(String, nullable=True)
    publication_year = Column(Integer, nullable=True)
    pages = Column(Integer, nullable=True)
    status = Column(Enum(BookStatus), default=BookStatus.available, nullable=False)
    borrower = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    genre_obj = relationship("Genre", back_populates="books")
    loans = relationship("Loan", back_populates="book")
    reservations = relationship("Reservation", back_populates="book")

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    borrower = Column(String, nullable=False)
    checkout_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False)
    returned_at = Column(DateTime, nullable=True)
    is_overdue = Column(Boolean, default=False, nullable=False)

    book = relationship("Book", back_populates="loans")

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    reserver = Column(String, nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.active, nullable=False)
    reserved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    book = relationship("Book", back_populates="reservations")