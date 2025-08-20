from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean
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

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=False, index=True)
    genre = Column(String, nullable=True, index=True)
    isbn = Column(String, nullable=True, index=True)
    status = Column(Enum(BookStatus), default=BookStatus.available, nullable=False)
    borrower = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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