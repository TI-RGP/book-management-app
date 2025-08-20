from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime

from .database import engine, get_db
from .models import Base, Book, BookStatus
from .routers import books

Base.metadata.create_all(bind=engine)

app = FastAPI(title="図書管理システム", description="貸し出し図書管理のWebアプリ")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(books.router)

@app.on_event("startup")
def create_sample_data():
    db = next(get_db())
    try:
        existing_books = db.query(Book).count()
        if existing_books == 0:
            sample_books = [
                Book(
                    title="Pythonプログラミング入門",
                    author="山田太郎",
                    status=BookStatus.available,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Book(
                    title="FastAPI実践ガイド",
                    author="佐藤花子",
                    status=BookStatus.available,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Book(
                    title="データベース設計",
                    author="田中次郎",
                    status=BookStatus.borrowed,
                    borrower="鈴木一郎",
                    due_date=datetime(2024, 1, 15),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            for book in sample_books:
                db.add(book)
            db.commit()
            print("サンプルデータを作成しました")
    finally:
        db.close()