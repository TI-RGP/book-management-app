from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import Optional

from ..database import get_db
from ..models import Book, Loan, Reservation, BookStatus, ReservationStatus
from .. import schemas

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    total_books = db.query(Book).count()
    available_books = db.query(Book).filter(Book.status == BookStatus.available).count()
    borrowed_books = db.query(Book).filter(Book.status == BookStatus.borrowed).count()
    
    recent_books = db.query(Book).order_by(Book.created_at.desc()).limit(5).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_books": total_books,
        "available_books": available_books,
        "borrowed_books": borrowed_books,
        "recent_books": recent_books
    })

@router.get("/books", response_class=HTMLResponse)
def books_list(
    request: Request, 
    q: Optional[str] = None,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Book)
    
    if q:
        query = query.filter(or_(
            Book.title.contains(q),
            Book.author.contains(q),
            Book.genre.contains(q) if Book.genre else False
        ))
    
    if author:
        query = query.filter(Book.author.contains(author))
    
    if genre:
        query = query.filter(Book.genre.contains(genre))
    
    if status:
        try:
            status_enum = BookStatus(status)
            query = query.filter(Book.status == status_enum)
        except ValueError:
            pass
    
    books = query.order_by(Book.created_at.desc()).all()
    
    return templates.TemplateResponse("books_list.html", {
        "request": request,
        "books": books,
        "search_query": q or "",
        "author_filter": author or "",
        "genre_filter": genre or "",
        "status_filter": status or ""
    })

@router.get("/books/new", response_class=HTMLResponse)
def book_new_form(request: Request):
    return templates.TemplateResponse("book_new.html", {"request": request})

@router.post("/books/new")
def create_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    genre: str = Form(""),
    isbn: str = Form(""),
    db: Session = Depends(get_db)
):
    if not title.strip() or not author.strip():
        return templates.TemplateResponse("book_new.html", {
            "request": request,
            "error": "タイトルと著者は必須です",
            "title": title,
            "author": author,
            "genre": genre,
            "isbn": isbn
        })
    
    db_book = Book(
        title=title.strip(), 
        author=author.strip(),
        genre=genre.strip() if genre.strip() else None,
        isbn=isbn.strip() if isbn.strip() else None
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    return RedirectResponse(url=f"/books/{db_book.id}", status_code=303)

@router.get("/books/{book_id}", response_class=HTMLResponse)
def book_detail(request: Request, book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    loans = db.query(Loan).filter(Loan.book_id == book_id).order_by(Loan.checkout_at.desc()).all()
    reservations = db.query(Reservation).filter(
        Reservation.book_id == book_id,
        Reservation.status == ReservationStatus.active
    ).order_by(Reservation.reserved_at.asc()).all()
    
    # Check for overdue loans
    now = datetime.now()
    for loan in loans:
        if loan.returned_at is None and loan.due_date < now:
            loan.is_overdue = True
            db.commit()
    
    return templates.TemplateResponse("book_detail.html", {
        "request": request,
        "book": book,
        "loans": loans,
        "reservations": reservations,
        "can_reserve": book.status == BookStatus.borrowed
    })

@router.get("/books/{book_id}/checkout", response_class=HTMLResponse)
def checkout_form(request: Request, book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.status == BookStatus.borrowed:
        return RedirectResponse(url=f"/books/{book_id}", status_code=303)
    
    default_due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
    return templates.TemplateResponse("checkout.html", {
        "request": request,
        "book": book,
        "default_due_date": default_due_date
    })

@router.post("/books/{book_id}/checkout")
def checkout_book(
    request: Request,
    book_id: int,
    borrower: str = Form(...),
    due_date: str = Form(...),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.status == BookStatus.borrowed:
        return RedirectResponse(url=f"/books/{book_id}", status_code=303)
    
    if not borrower.strip():
        default_due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        return templates.TemplateResponse("checkout.html", {
            "request": request,
            "book": book,
            "error": "借り手名は必須です",
            "borrower": borrower,
            "due_date": due_date,
            "default_due_date": default_due_date
        })
    
    try:
        due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        default_due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        return templates.TemplateResponse("checkout.html", {
            "request": request,
            "book": book,
            "error": "正しい日付を入力してください",
            "borrower": borrower,
            "due_date": due_date,
            "default_due_date": default_due_date
        })
    
    book.status = BookStatus.borrowed
    book.borrower = borrower.strip()
    book.due_date = due_date_obj
    book.updated_at = datetime.utcnow()
    
    loan = Loan(
        book_id=book_id,
        borrower=borrower.strip(),
        due_date=due_date_obj
    )
    db.add(loan)
    db.commit()
    
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)

@router.post("/books/{book_id}/return")
def return_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.status == BookStatus.available:
        return RedirectResponse(url=f"/books/{book_id}", status_code=303)
    
    book.status = BookStatus.available
    book.borrower = None
    book.due_date = None
    book.updated_at = datetime.utcnow()
    
    active_loan = db.query(Loan).filter(
        Loan.book_id == book_id,
        Loan.returned_at.is_(None)
    ).first()
    
    if active_loan:
        active_loan.returned_at = datetime.utcnow()
    
    db.commit()
    
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)

# 予約機能
@router.post("/books/{book_id}/reserve")
def reserve_book(
    request: Request,
    book_id: int,
    reserver: str = Form(...),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.status == BookStatus.available:
        return RedirectResponse(url=f"/books/{book_id}", status_code=303)
    
    if not reserver.strip():
        return RedirectResponse(url=f"/books/{book_id}", status_code=303)
    
    # Check if user already has active reservation
    existing_reservation = db.query(Reservation).filter(
        Reservation.book_id == book_id,
        Reservation.reserver == reserver.strip(),
        Reservation.status == ReservationStatus.active
    ).first()
    
    if existing_reservation:
        return RedirectResponse(url=f"/books/{book_id}", status_code=303)
    
    reservation = Reservation(
        book_id=book_id,
        reserver=reserver.strip()
    )
    db.add(reservation)
    db.commit()
    
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)

@router.post("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    reservation.status = ReservationStatus.cancelled
    db.commit()
    
    return RedirectResponse(url=f"/books/{reservation.book_id}", status_code=303)

# 貸出履歴と統計
@router.get("/loans", response_class=HTMLResponse)
def loans_history(request: Request, db: Session = Depends(get_db)):
    loans = db.query(Loan).order_by(Loan.checkout_at.desc()).limit(100).all()
    overdue_loans = db.query(Loan).filter(
        Loan.returned_at.is_(None),
        Loan.due_date < datetime.now()
    ).all()
    
    return templates.TemplateResponse("loans_history.html", {
        "request": request,
        "loans": loans,
        "overdue_loans": overdue_loans
    })

# 延滞管理
@router.get("/overdue", response_class=HTMLResponse)
def overdue_books(request: Request, db: Session = Depends(get_db)):
    now = datetime.now()
    overdue_loans = db.query(Loan).filter(
        Loan.returned_at.is_(None),
        Loan.due_date < now
    ).order_by(Loan.due_date.asc()).all()
    
    # Mark as overdue
    for loan in overdue_loans:
        if not loan.is_overdue:
            loan.is_overdue = True
    db.commit()
    
    return templates.TemplateResponse("overdue_books.html", {
        "request": request,
        "overdue_loans": overdue_loans
    })

# 予約一覧
@router.get("/reservations", response_class=HTMLResponse)
def reservations_list(request: Request, db: Session = Depends(get_db)):
    active_reservations = db.query(Reservation).filter(
        Reservation.status == ReservationStatus.active
    ).order_by(Reservation.reserved_at.asc()).all()
    
    return templates.TemplateResponse("reservations_list.html", {
        "request": request,
        "reservations": active_reservations
    })