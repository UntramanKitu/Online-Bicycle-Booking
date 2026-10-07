from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.eakapol import LostItem
from app.schemas.eakapol import LostItemCreate, LostItemUpdate, LostItemResponse
from app.models.unified_user import UnifiedUser
from app.models.bicycle import Bicycle

router = APIRouter(prefix="/api/lost-items", tags=["Lost Items"])


def resolve_user(user_id: int, db: Session):
    user = db.get(UnifiedUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def resolve_bicycle(bicycle_id: int, db: Session):
    bike = db.get(Bicycle, bicycle_id)
    if not bike:
        raise HTTPException(status_code=404, detail="Bicycle not found")
    return bike


@router.get("", response_model=List[LostItemResponse])
def list_lost_items(db: Session = Depends(get_db)):
    return db.query(LostItem).order_by(LostItem.created_at.desc()).all()


@router.get("/{item_id}", response_model=LostItemResponse)
def get_lost_item(item_id: int, db: Session = Depends(get_db)):
    record = db.query(LostItem).filter(LostItem.id == item_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Lost item not found")
    return record


@router.get("/user/{user_id}", response_model=List[LostItemResponse])
def list_user_lost_items(user_id: int, db: Session = Depends(get_db)):
    return db.query(LostItem).filter(
        LostItem.user_id == user_id
    ).order_by(LostItem.created_at.desc()).all()


@router.post("", response_model=LostItemResponse, status_code=201)
def create_lost_item(data: LostItemCreate, db: Session = Depends(get_db)):
    user = resolve_user(int(data.user_id), db)
    payload = {**data.model_dump(), "user_id": user.id}
    if data.bicycle_id is not None:
        bike = resolve_bicycle(int(data.bicycle_id), db)
        payload["bicycle_id"] = bike.id
    record = LostItem(**payload)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{item_id}", response_model=LostItemResponse)
def update_lost_item(item_id: int, data: LostItemUpdate, db: Session = Depends(get_db)):
    record = db.query(LostItem).filter(LostItem.id == item_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Lost item not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{item_id}", status_code=204)
def delete_lost_item(item_id: int, db: Session = Depends(get_db)):
    record = db.query(LostItem).filter(LostItem.id == item_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Lost item not found")
    db.delete(record)
    db.commit()
