from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import PointsLog
from schemas import PointsLogCreate, PointsLogResponse
from utils import resolve_user

router = APIRouter(prefix="/api/points", tags=["Points Log"])


@router.get("/", response_model=List[PointsLogResponse])
def list_points_log(db: Session = Depends(get_db)):
    return db.query(PointsLog).order_by(PointsLog.created_at.desc()).all()


@router.get("/user/{user_id}", response_model=List[PointsLogResponse])
def list_user_points(user_id: int, db: Session = Depends(get_db)):
    return db.query(PointsLog).filter(
        PointsLog.user_id == user_id
    ).order_by(PointsLog.created_at.desc()).all()


@router.post("/add", response_model=PointsLogResponse, status_code=201)
def add_points(data: PointsLogCreate, db: Session = Depends(get_db)):
    user = resolve_user(data.user_id, db)
    payload = {**data.model_dump(), "user_id": user.id}
    record = PointsLog(**payload)
    db.add(record)
    db.flush()

    user.points = max(0, user.points + data.points)
    db.commit()
    db.refresh(record)
    return record