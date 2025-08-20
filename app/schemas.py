from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .models import BookStatus, ReservationStatus

class GenreBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    level: int = 1
    description: Optional[str] = None

class GenreCreate(GenreBase):
    pass

class GenreUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None

class Genre(GenreBase):
    id: int
    created_at: datetime
    updated_at: datetime
    children: List['Genre'] = []

    class Config:
        from_attributes = True

class BookBase(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    genre_id: Optional[int] = None
    genre: Optional[str] = None  # For backward compatibility
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    pages: Optional[int] = None

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    genre_id: Optional[int] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    pages: Optional[int] = None

class Book(BookBase):
    id: int
    status: BookStatus
    borrower: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    genre_obj: Optional[Genre] = None

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
    genre_id: Optional[int] = None
    status: Optional[BookStatus] = None

# Fix forward reference
Genre.model_rebuild()