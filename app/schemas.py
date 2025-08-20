from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .models import BookStatus, ReservationStatus

class BookBase(BaseModel):
    title: str
    author: str
    genre: Optional[str] = None
    isbn: Optional[str] = None

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    status: BookStatus
    borrower: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CheckoutRequest(BaseModel):
    borrower: str
    due_date: datetime

class LoanBase(BaseModel):
    borrower: str
    due_date: datetime

class LoanCreate(LoanBase):
    book_id: int

class Loan(LoanBase):
    id: int
    book_id: int
    checkout_at: datetime
    returned_at: Optional[datetime] = None
    is_overdue: bool = False

    class Config:
        from_attributes = True

class ReservationBase(BaseModel):
    reserver: str

class ReservationCreate(ReservationBase):
    book_id: int

class Reservation(ReservationBase):
    id: int
    book_id: int
    status: ReservationStatus
    reserved_at: datetime
    notified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BookWithHistory(Book):
    loans: List[Loan] = []
    reservations: List[Reservation] = []

class SearchRequest(BaseModel):
    query: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    status: Optional[BookStatus] = None