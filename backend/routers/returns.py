from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import ReturnRecord
from schemas import ReturnRecordCreate, ReturnRecordUpdate, ReturnRecordResponse

router = APIRouter(prefix="/api/returns", tags=["Returns"])


@router.get("/", response_model=List[ReturnRecordResponse])
def list_returns(db: Session = Depends(get_db)):
    return db.query(ReturnRecord).order_by(ReturnRecord.created_at.desc()).all()


@router.get("/{return_id}", response_model=ReturnRecordResponse)
def get_return(return_id: int, db: Session = Depends(get_db)):
    record = db.query(ReturnRecord).filter(ReturnRecord.id == return_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Return record not found")
    return record


@router.post("/", response_model=ReturnRecordResponse, status_code=201)
def create_return(data: ReturnRecordCreate, db: Session = Depends(get_db)):
    record = ReturnRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{return_id}", response_model=ReturnRecordResponse)
def update_return(return_id: int, data: ReturnRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(ReturnRecord).filter(ReturnRecord.id == return_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Return record not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{return_id}", status_code=204)
def delete_return(return_id: int, db: Session = Depends(get_db)):
    record = db.query(ReturnRecord).filter(ReturnRecord.id == return_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Return record not found")
    db.delete(record)
    db.commit()
