from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.eakapol import PenaltyStrike, PenaltyReason
from app.schemas.eakapol import PenaltyStrikeCreate, PenaltyStrikeUpdate, PenaltyStrikeResponse
from app.models.unified_user import UnifiedUser

router = APIRouter(prefix="/api/penalties", tags=["Penalties"])

MAX_POINTS = 12
POSITIVE_REASONS = {PenaltyReason.GOOD_BEHAVIOR, PenaltyReason.NO_VIOLATION_WEEK}


def resolve_user(user_id: int, db: Session):
    user = db.get(UnifiedUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _apply_points(user: UnifiedUser, reason: str, magnitude: int) -> None:
    delta = magnitude if reason in POSITIVE_REASONS else -magnitude
    if user.points is None:
        user.points = 12
    user.points = min(MAX_POINTS, max(0, user.points + delta))


@router.get("", response_model=List[PenaltyStrikeResponse])
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


@router.post("", response_model=PenaltyStrikeResponse, status_code=201)
def create_penalty(data: PenaltyStrikeCreate, db: Session = Depends(get_db)):
    user = resolve_user(int(data.user_id), db)
    valid_reasons = {r.value for r in PenaltyReason}
    if data.reason not in valid_reasons:
        raise HTTPException(status_code=422, detail=f"reason ต้องเป็นหนึ่งใน {sorted(valid_reasons)}")

    record = PenaltyStrike(**{**data.model_dump(), "user_id": user.id, "user_id": int(data.user_id)})
    db.add(record)
    db.flush()
    _apply_points(user, data.reason, data.penalty_points)
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
