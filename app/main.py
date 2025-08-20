from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime

from .database import engine, get_db
from .models import Base, Book, BookStatus, Genre, Employee, EmployeeStatus
from .routers import books, genres, employees

Base.metadata.create_all(bind=engine)

app = FastAPI(title="図書管理システム", description="貸し出し図書管理のWebアプリ")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(books.router)
app.include_router(genres.router)
app.include_router(employees.router)

@app.on_event("startup")
def create_sample_data():
    db = next(get_db())
    try:
        # Only create sample data if no data exists (not on every deployment)
        existing_genres = db.query(Genre).count()
        existing_books = db.query(Book).count()
        existing_employees = db.query(Employee).count()
        
        # Skip if data already exists
        if existing_genres > 0 or existing_books > 0:
            print("Data already exists, skipping sample data creation")
            return
        
        print("Creating sample data...")
        
        # Create sample employees first
        if existing_employees == 0:
            sample_employees = [
                Employee(
                    employee_id="E001",
                    name="田中太郎",
                    name_kana="タナカタロウ",
                    email="tanaka@company.com",
                    department="システム開発部",
                    position="シニアエンジニア",
                    phone="03-1234-5678",
                    hire_date=datetime(2020, 4, 1),
                    status=EmployeeStatus.active,
                    notes="Pythonエンジニア"
                ),
                Employee(
                    employee_id="E002",
                    name="佐藤花子",
                    name_kana="サトウハナコ",
                    email="sato@company.com",
                    department="プロジェクト管理部",
                    position="プロジェクトマネージャー",
                    phone="03-1234-5679",
                    hire_date=datetime(2019, 7, 15),
                    status=EmployeeStatus.active,
                    notes="アジャイル開発専門"
                ),
                Employee(
                    employee_id="E003",
                    name="鈴木一郎",
                    name_kana="スズキイチロウ",
                    email="suzuki@company.com",
                    department="データ分析部",
                    position="データアナリスト",
                    phone="03-1234-5680",
                    hire_date=datetime(2021, 1, 10),
                    status=EmployeeStatus.active,
                    notes="機械学習・統計分析"
                )
            ]
            
            for employee in sample_employees:
                db.add(employee)
            db.commit()
            print("サンプル社員データを作成しました")
        
        # Create sample genres if they don't exist
        if existing_genres == 0:
            sample_genres = [
                Genre(name="技術書", level=1, description="プログラミングや技術関連の書籍"),
                Genre(name="文学", level=1, description="小説や詩集など"),
                Genre(name="ビジネス", level=1, description="経営やビジネススキル関連"),
                Genre(name="プログラミング", parent_id=1, level=2, description="プログラミング言語や開発手法"),
                Genre(name="データベース", parent_id=1, level=2, description="データベース設計や管理"),
                Genre(name="小説", parent_id=2, level=2, description="フィクション作品"),
                Genre(name="Python", parent_id=4, level=3, description="Python言語関連"),
                Genre(name="Web開発", parent_id=4, level=3, description="Web開発技術"),
            ]
            
            for genre in sample_genres:
                db.add(genre)
            db.commit()
            
            # Update parent_id for child genres
            for genre in sample_genres:
                if genre.level > 1:
                    parent_name_map = {
                        "プログラミング": "技術書",
                        "データベース": "技術書", 
                        "小説": "文学",
                        "Python": "プログラミング",
                        "Web開発": "プログラミング"
                    }
                    if genre.name in parent_name_map:
                        parent = db.query(Genre).filter(Genre.name == parent_name_map[genre.name]).first()
                        if parent:
                            genre.parent_id = parent.id
            db.commit()
        
        # Create sample books
        print("Creating sample books...")
        # Get sample genres for books
        python_genre = db.query(Genre).filter(Genre.name == "Python").first()
        web_genre = db.query(Genre).filter(Genre.name == "Web開発").first()
        db_genre = db.query(Genre).filter(Genre.name == "データベース").first()
        
        sample_books = [
            Book(
                    title="Pythonプログラミング入門",
                    author="山田太郎",
                    description="Pythonの基礎から応用まで学べる入門書です。初心者にもわかりやすく解説されています。",
                    genre_id=python_genre.id if python_genre else None,
                    isbn="978-4-123456-78-9",
                    publisher="技術出版社",
                    publication_year=2023,
                    pages=350,
                    status=BookStatus.available,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Book(
                    title="FastAPI実践ガイド",
                    author="佐藤花子",
                    description="FastAPIを使ったWebアプリケーション開発の実践的なガイドブックです。",
                    genre_id=web_genre.id if web_genre else None,
                    isbn="978-4-987654-32-1",
                    publisher="Web開発出版",
                    publication_year=2023,
                    pages=280,
                    status=BookStatus.available,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                Book(
                    title="データベース設計",
                    author="田中次郎",
                    description="効率的なデータベース設計の手法とベストプラクティスを解説した専門書です。",
                    genre_id=db_genre.id if db_genre else None,
                    isbn="978-4-555666-77-8",
                    publisher="データベース出版",
                    publication_year=2022,
                    pages=420,
                    status=BookStatus.borrowed,
                    borrower="鈴木一郎",
                    borrower_employee_id=3,  # E003 - 鈴木一郎
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