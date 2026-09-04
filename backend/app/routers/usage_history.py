from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.crud.booking import (
    get_usage_history, get_usage_histories, get_usage_histories_by_user,
    get_usage_histories_by_bicycle, get_usage_histories_by_booking,
    create_usage_history, update_usage_history, delete_usage_history,
)
from app.schemas.booking import (
    UsageHistoryLogCreate, UsageHistoryLogUpdate, UsageHistoryLogResponse,
)

router = APIRouter()


@router.get("/usage-histories", response_model=List[UsageHistoryLogResponse])
def list_usage_histories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    bicycle_id: Optional[int] = None,
    booking_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    if user_id:
        return get_usage_histories_by_user(db, user_id, skip=skip, limit=limit)
    if bicycle_id:
        return get_usage_histories_by_bicycle(db, bicycle_id, skip=skip, limit=limit)
    if booking_id:
        result = get_usage_histories_by_booking(db, booking_id)
        return [result] if result else []
    return get_usage_histories(db, skip=skip, limit=limit)


@router.get("/usage-histories/{history_id}", response_model=UsageHistoryLogResponse)
def read_usage_history(history_id: int, db: Session = Depends(get_db)):
    db_history = get_usage_history(db, history_id)
    if db_history is None:
        raise HTTPException(status_code=404, detail="Usage history not found")
    return db_history


@router.post("/usage-histories", response_model=UsageHistoryLogResponse, status_code=201)
def create_new_usage_history(history: UsageHistoryLogCreate, db: Session = Depends(get_db)):
    return create_usage_history(db, history)


@router.put("/usage-histories/{history_id}", response_model=UsageHistoryLogResponse)
def update_existing_usage_history(history_id: int, history: UsageHistoryLogUpdate, db: Session = Depends(get_db)):
    db_history = update_usage_history(db, history_id, history)
    if db_history is None:
        raise HTTPException(status_code=404, detail="Usage history not found")
    return db_history


@router.delete("/usage-histories/{history_id}", status_code=204)
def delete_existing_usage_history(history_id: int, db: Session = Depends(get_db)):
    deleted = delete_usage_history(db, history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usage history not found")
    return None