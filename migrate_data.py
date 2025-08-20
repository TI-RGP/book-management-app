#!/usr/bin/env python3
"""
Data migration script for moving from SQLite to PostgreSQL
Run this script to migrate existing data when switching databases
"""
import os
import sys
import sqlite3
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, engine
from app.models import Base, Book, Genre, Loan, Reservation, BookStatus, ReservationStatus

def migrate_from_sqlite():
    """Migrate data from SQLite to PostgreSQL"""
    
    # Check if SQLite database exists
    sqlite_path = "./library.db"
    if not os.path.exists(sqlite_path):
        print("No SQLite database found at ./library.db")
        return
    
    print("Starting data migration from SQLite to PostgreSQL...")
    
    # Create all tables in the target database
    Base.metadata.create_all(bind=engine)
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to target database (PostgreSQL)
    db = SessionLocal()
    
    try:
        # Migrate Genres
        print("Migrating genres...")
        sqlite_cursor.execute("SELECT * FROM genres ORDER BY level, name")
        genres = sqlite_cursor.fetchall()
        
        genre_id_map = {}  # Map old IDs to new IDs
        
        for genre_row in genres:
            genre = Genre(
                name=genre_row['name'],
                parent_id=None,  # Will be updated in second pass
                level=genre_row['level'],
                description=genre_row['description'],
                created_at=datetime.fromisoformat(genre_row['created_at']) if genre_row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(genre_row['updated_at']) if genre_row['updated_at'] else datetime.utcnow()
            )
            db.add(genre)
            db.flush()  # Get the new ID
            genre_id_map[genre_row['id']] = genre.id
        
        db.commit()
        
        # Update parent_id relationships
        print("Updating genre parent relationships...")
        for genre_row in genres:
            if genre_row['parent_id']:
                genre = db.query(Genre).filter(Genre.id == genre_id_map[genre_row['id']]).first()
                if genre and genre_row['parent_id'] in genre_id_map:
                    genre.parent_id = genre_id_map[genre_row['parent_id']]
        
        db.commit()
        
        # Migrate Books
        print("Migrating books...")
        sqlite_cursor.execute("SELECT * FROM books")
        books = sqlite_cursor.fetchall()
        
        book_id_map = {}
        
        for book_row in books:
            # Map genre_id if it exists
            mapped_genre_id = None
            if book_row['genre_id'] and book_row['genre_id'] in genre_id_map:
                mapped_genre_id = genre_id_map[book_row['genre_id']]
            
            book = Book(
                title=book_row['title'],
                author=book_row['author'],
                description=book_row['description'],
                genre_id=mapped_genre_id,
                genre=book_row['genre'],  # Backward compatibility field
                isbn=book_row['isbn'],
                publisher=book_row['publisher'],
                publication_year=book_row['publication_year'],
                pages=book_row['pages'],
                status=BookStatus(book_row['status']),
                borrower=book_row['borrower'],
                due_date=datetime.fromisoformat(book_row['due_date']) if book_row['due_date'] else None,
                created_at=datetime.fromisoformat(book_row['created_at']) if book_row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(book_row['updated_at']) if book_row['updated_at'] else datetime.utcnow()
            )
            db.add(book)
            db.flush()
            book_id_map[book_row['id']] = book.id
        
        db.commit()
        
        # Migrate Loans
        print("Migrating loans...")
        try:
            sqlite_cursor.execute("SELECT * FROM loans")
            loans = sqlite_cursor.fetchall()
            
            for loan_row in loans:
                if loan_row['book_id'] in book_id_map:
                    loan = Loan(
                        book_id=book_id_map[loan_row['book_id']],
                        borrower=loan_row['borrower'],
                        checkout_at=datetime.fromisoformat(loan_row['checkout_at']) if loan_row['checkout_at'] else datetime.utcnow(),
                        due_date=datetime.fromisoformat(loan_row['due_date']) if loan_row['due_date'] else datetime.utcnow(),
                        returned_at=datetime.fromisoformat(loan_row['returned_at']) if loan_row['returned_at'] else None,
                        is_overdue=bool(loan_row['is_overdue']) if 'is_overdue' in loan_row.keys() else False
                    )
                    db.add(loan)
            
            db.commit()
        except sqlite3.OperationalError:
            print("No loans table found in SQLite database, skipping...")
        
        # Migrate Reservations
        print("Migrating reservations...")
        try:
            sqlite_cursor.execute("SELECT * FROM reservations")
            reservations = sqlite_cursor.fetchall()
            
            for res_row in reservations:
                if res_row['book_id'] in book_id_map:
                    reservation = Reservation(
                        book_id=book_id_map[res_row['book_id']],
                        reserver=res_row['reserver'],
                        status=ReservationStatus(res_row['status']),
                        reserved_at=datetime.fromisoformat(res_row['reserved_at']) if res_row['reserved_at'] else datetime.utcnow(),
                        notified_at=datetime.fromisoformat(res_row['notified_at']) if res_row['notified_at'] else None,
                        expires_at=datetime.fromisoformat(res_row['expires_at']) if res_row['expires_at'] else None
                    )
                    db.add(reservation)
            
            db.commit()
        except sqlite3.OperationalError:
            print("No reservations table found in SQLite database, skipping...")
        
        print("Data migration completed successfully!")
        print(f"Migrated:")
        print(f"  - {len(genres)} genres")
        print(f"  - {len(books)} books")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        sqlite_conn.close()

if __name__ == "__main__":
    migrate_from_sqlite()