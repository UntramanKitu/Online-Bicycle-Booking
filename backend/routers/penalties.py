from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import PenaltyStrike, PointsLog
from schemas import PenaltyStrikeCreate, PenaltyStrikeUpdate, PenaltyStrikeResponse
from utils import resolve_user

router = APIRouter(prefix="/api/penalties", tags=["Penalties"])


@router.get("/", response_model=List[PenaltyStrikeResponse])
def list_penalties(db: Session = Depends(get_db)):
    return db.query(PenaltyStrike).order_by(PenaltyStrike.created_at.desc()).all()


@router.get("/{penalty_id}", response_model=PenaltyStrikeResponse)
def get_penalty(penalty_id: int, db: Session = Depends(get_db)):
    record = db.query(PenaltyStrike).filter(PenaltyStrike.id == penalty_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Penalty not found")
    return record


@router.get("/user/{user_id}", response_model=List[PenaltyStrikeResponse])
def list_user_penalties(user_id: int, db: Session = Depends(get_db)):
    return db.query(PenaltyStrike).filter(
        PenaltyStrike.user_id == user_id
    ).order_by(PenaltyStrike.created_at.desc()).all()


@router.post("/", response_model=PenaltyStrikeResponse, status_code=201)
def create_penalty(data: PenaltyStrikeCreate, db: Session = Depends(get_db)):
    user = resolve_user(data.user_id, db)

    record = PenaltyStrike(**{**data.model_dump(), "user_id": user.id})
    db.add(record)
    db.flush()

    user.points = max(0, user.points - data.penalty_points)

    log = PointsLog(
        user_id=user.id,
        points=-data.penalty_points,
        reason=data.reason,
        description=data.description or f"หัก {data.penalty_points} แต้ม: {data.reason}",
        penalty_id=record.id,
    )
    db.add(log)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{penalty_id}", response_model=PenaltyStrikeResponse)
def update_penalty(penalty_id: int, data: PenaltyStrikeUpdate, db: Session = Depends(get_db)):
    record = db.query(PenaltyStrike).filter(PenaltyStrike.id == penalty_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Penalty not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{penalty_id}", status_code=204)
def delete_penalty(penalty_id: int, db: Session = Depends(get_db)):
    record = db.query(PenaltyStrike).filter(PenaltyStrike.id == penalty_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Penalty not found")
    db.delete(record)
    db.commit()