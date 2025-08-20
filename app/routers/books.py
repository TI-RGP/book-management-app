from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import Optional

from ..database import get_db
from ..models import Book, Loan, BookStatus
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
def books_list(request: Request, q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Book)
    
    if q:
        query = query.filter(or_(
            Book.title.contains(q),
            Book.author.contains(q)
        ))
    
    books = query.order_by(Book.created_at.desc()).all()
    
    return templates.TemplateResponse("books_list.html", {
        "request": request,
        "books": books,
        "search_query": q or ""
    })

@router.get("/books/new", response_class=HTMLResponse)
def book_new_form(request: Request):
    return templates.TemplateResponse("book_new.html", {"request": request})

@router.post("/books/new")
def create_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    db: Session = Depends(get_db)
):
    if not title.strip() or not author.strip():
        return templates.TemplateResponse("book_new.html", {
            "request": request,
            "error": "タイトルと著者は必須です",
            "title": title,
            "author": author
        })
    
    db_book = Book(title=title.strip(), author=author.strip())
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
    
    return templates.TemplateResponse("book_detail.html", {
        "request": request,
        "book": book,
        "loans": loans
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