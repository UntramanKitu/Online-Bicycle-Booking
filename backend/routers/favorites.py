from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Favorite
from schemas import FavoriteCreate, FavoriteUpdate, FavoriteResponse

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])


@router.get("/", response_model=List[FavoriteResponse])
def list_favorites(db: Session = Depends(get_db)):
    return db.query(Favorite).order_by(Favorite.created_at.desc()).all()


@router.get("/{favorite_id}", response_model=FavoriteResponse)
def get_favorite(favorite_id: int, db: Session = Depends(get_db)):
    record = db.query(Favorite).filter(Favorite.id == favorite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return record


@router.get("/user/{user_id}", response_model=List[FavoriteResponse])
def list_user_favorites(user_id: str, db: Session = Depends(get_db)):
    return db.query(Favorite).filter(
        Favorite.user_id == user_id
    ).order_by(Favorite.created_at.desc()).all()


@router.post("/", response_model=FavoriteResponse, status_code=201)
def create_favorite(data: FavoriteCreate, db: Session = Depends(get_db)):
    record = Favorite(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{favorite_id}", response_model=FavoriteResponse)
def update_favorite(favorite_id: int, data: FavoriteUpdate, db: Session = Depends(get_db)):
    record = db.query(Favorite).filter(Favorite.id == favorite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Favorite not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{favorite_id}", status_code=204)
def delete_favorite(favorite_id: int, db: Session = Depends(get_db)):
    record = db.query(Favorite).filter(Favorite.id == favorite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(record)
    db.commit()
