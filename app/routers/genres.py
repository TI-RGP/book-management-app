from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from ..models import Genre
from .. import schemas

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/genres", response_class=HTMLResponse)
def genres_list(request: Request, db: Session = Depends(get_db)):
    # Get all genres with their hierarchical structure
    root_genres = db.query(Genre).filter(Genre.parent_id.is_(None)).order_by(Genre.name).all()
    
    def build_genre_tree(parent_genres):
        tree = []
        for genre in parent_genres:
            children = db.query(Genre).filter(Genre.parent_id == genre.id).order_by(Genre.name).all()
            genre_data = {
                'genre': genre,
                'children': build_genre_tree(children) if children else []
            }
            tree.append(genre_data)
        return tree
    
    genre_tree = build_genre_tree(root_genres)
    
    return templates.TemplateResponse("genres_list.html", {
        "request": request,
        "genre_tree": genre_tree
    })

@router.get("/genres/new", response_class=HTMLResponse)
def genre_new_form(request: Request, parent_id: Optional[int] = None, db: Session = Depends(get_db)):
    parent_genre = None
    if parent_id:
        parent_genre = db.query(Genre).filter(Genre.id == parent_id).first()
        if not parent_genre:
            raise HTTPException(status_code=404, detail="Parent genre not found")
    
    # Get genres for parent selection (only levels 1 and 2 can be parents)
    all_genres = db.query(Genre).filter(Genre.level < 3).order_by(Genre.level, Genre.name).all()
    
    return templates.TemplateResponse("genre_new.html", {
        "request": request,
        "parent_genre": parent_genre,
        "all_genres": all_genres
    })

@router.post("/genres/new")
def create_genre(
    request: Request,
    name: str = Form(...),
    parent_id: Optional[str] = Form(None),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    if not name.strip():
        all_genres = db.query(Genre).filter(Genre.level < 3).order_by(Genre.level, Genre.name).all()
        return templates.TemplateResponse("genre_new.html", {
            "request": request,
            "error": "ジャンル名は必須です",
            "name": name,
            "description": description,
            "all_genres": all_genres
        })
    
    # Check for duplicate names
    existing_genre = db.query(Genre).filter(Genre.name == name.strip()).first()
    if existing_genre:
        all_genres = db.query(Genre).filter(Genre.level < 3).order_by(Genre.level, Genre.name).all()
        return templates.TemplateResponse("genre_new.html", {
            "request": request,
            "error": "このジャンル名は既に存在します",
            "name": name,
            "description": description,
            "all_genres": all_genres
        })
    
    # Determine level based on parent
    level = 1
    parent_genre_id = None
    if parent_id and parent_id.strip():
        try:
            parent_genre_id = int(parent_id)
            parent_genre = db.query(Genre).filter(Genre.id == parent_genre_id).first()
            if parent_genre:
                level = parent_genre.level + 1
                if level > 3:  # Max 3 levels
                    all_genres = db.query(Genre).filter(Genre.level < 3).order_by(Genre.level, Genre.name).all()
                    return templates.TemplateResponse("genre_new.html", {
                        "request": request,
                        "error": "ジャンルは3階層までです",
                        "name": name,
                        "description": description,
                        "all_genres": all_genres
                    })
        except ValueError:
            parent_genre_id = None
    
    db_genre = Genre(
        name=name.strip(),
        parent_id=parent_genre_id,
        level=level,
        description=description.strip() if description.strip() else None
    )
    db.add(db_genre)
    db.commit()
    db.refresh(db_genre)
    
    return RedirectResponse(url="/genres", status_code=303)

@router.get("/genres/{genre_id}/edit", response_class=HTMLResponse)
def genre_edit_form(request: Request, genre_id: int, db: Session = Depends(get_db)):
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    
    # Get genres for parent selection (exclude self and descendants, max level 2 can be parent)
    all_genres = db.query(Genre).filter(
        Genre.id != genre_id, 
        Genre.level < 3
    ).order_by(Genre.level, Genre.name).all()
    
    return templates.TemplateResponse("genre_edit.html", {
        "request": request,
        "genre": genre,
        "all_genres": all_genres
    })

@router.post("/genres/{genre_id}/edit")
def update_genre(
    request: Request,
    genre_id: int,
    name: str = Form(...),
    parent_id: Optional[str] = Form(None),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    
    if not name.strip():
        all_genres = db.query(Genre).filter(Genre.id != genre_id, Genre.level < 3).order_by(Genre.level, Genre.name).all()
        return templates.TemplateResponse("genre_edit.html", {
            "request": request,
            "error": "ジャンル名は必須です",
            "genre": genre,
            "all_genres": all_genres
        })
    
    # Check for duplicate names (excluding current genre)
    existing_genre = db.query(Genre).filter(
        Genre.name == name.strip(),
        Genre.id != genre_id
    ).first()
    if existing_genre:
        all_genres = db.query(Genre).filter(Genre.id != genre_id, Genre.level < 3).order_by(Genre.level, Genre.name).all()
        return templates.TemplateResponse("genre_edit.html", {
            "request": request,
            "error": "このジャンル名は既に存在します",
            "genre": genre,
            "all_genres": all_genres
        })
    
    # Update genre
    genre.name = name.strip()
    genre.description = description.strip() if description.strip() else None
    
    # Handle parent change
    if parent_id and parent_id.strip():
        try:
            new_parent_id = int(parent_id)
            if new_parent_id != genre.parent_id:
                parent_genre = db.query(Genre).filter(Genre.id == new_parent_id).first()
                if parent_genre:
                    new_level = parent_genre.level + 1
                    if new_level <= 3:
                        genre.parent_id = new_parent_id
                        genre.level = new_level
        except ValueError:
            pass
    else:
        genre.parent_id = None
        genre.level = 1
    
    db.commit()
    
    return RedirectResponse(url="/genres", status_code=303)

@router.post("/genres/{genre_id}/delete")
def delete_genre(genre_id: int, db: Session = Depends(get_db)):
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    
    # Check if genre has children
    children = db.query(Genre).filter(Genre.parent_id == genre_id).first()
    if children:
        return RedirectResponse(url="/genres?error=has_children", status_code=303)
    
    # Check if genre is used by books
    from ..models import Book
    books_using_genre = db.query(Book).filter(Book.genre_id == genre_id).first()
    if books_using_genre:
        return RedirectResponse(url="/genres?error=has_books", status_code=303)
    
    db.delete(genre)
    db.commit()
    
    return RedirectResponse(url="/genres", status_code=303)

# API endpoints for dropdown population
@router.get("/api/genres")
def get_genres_api(db: Session = Depends(get_db)):
    genres = db.query(Genre).order_by(Genre.level, Genre.name).all()
    return [{"id": g.id, "name": g.name, "level": g.level, "parent_id": g.parent_id} for g in genres]

@router.get("/api/genres/tree")
def get_genres_tree_api(db: Session = Depends(get_db)):
    def build_tree(parent_id=None):
        genres = db.query(Genre).filter(Genre.parent_id == parent_id).order_by(Genre.name).all()
        tree = []
        for genre in genres:
            tree.append({
                "id": genre.id,
                "name": genre.name,
                "level": genre.level,
                "children": build_tree(genre.id)
            })
        return tree
    
    return build_tree()