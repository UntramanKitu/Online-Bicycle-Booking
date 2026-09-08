from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Favorite
from schemas import FavoriteCreate, FavoriteUpdate, FavoriteResponse
from utils import resolve_user, resolve_bicycle, get_actor, require_owner_or_admin, Actor

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
def list_user_favorites(user_id: int, db: Session = Depends(get_db)):
    return db.query(Favorite).filter(
        Favorite.user_id == user_id
    ).order_by(Favorite.created_at.desc()).all()


@router.post("/", response_model=FavoriteResponse, status_code=201)
def create_favorite(data: FavoriteCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_actor)):
    user = resolve_user(data.user_id, db)
    role, actor_id = actor
    if role != "admin" and actor_id != user.id:
        raise HTTPException(status_code=403, detail="ผู้ใช้ทั่วไปเพิ่มรายการโปรดได้เฉพาะของตัวเองเท่านั้น")
    payload = {**data.model_dump(), "user_id": user.id}
    if data.bicycle_id is not None:
        bike = resolve_bicycle(data.bicycle_id, db)
        payload["bicycle_id"] = bike.id
    record = Favorite(**payload)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{favorite_id}", response_model=FavoriteResponse)
def update_favorite(favorite_id: int, data: FavoriteUpdate, db: Session = Depends(get_db), actor: Actor = Depends(get_actor)):
    record = db.query(Favorite).filter(Favorite.id == favorite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Favorite not found")
    require_owner_or_admin(record.user_id, actor)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{favorite_id}", status_code=204)
def delete_favorite(favorite_id: int, db: Session = Depends(get_db), actor: Actor = Depends(get_actor)):
    record = db.query(Favorite).filter(Favorite.id == favorite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Favorite not found")
    require_owner_or_admin(record.user_id, actor)
    db.delete(record)
    db.commit()
