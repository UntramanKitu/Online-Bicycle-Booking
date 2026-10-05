"""M15 Feedback & Rating: รีวิวและให้คะแนนจักรยาน (1-5 ดาว)"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Review, ensure_user_and_bicycle

router = APIRouter(prefix="/api/reviews", tags=["Feedback & Rating"])


# ---------- รูปแบบข้อมูลเข้า/ออก ----------
class ReviewCreate(BaseModel):
    user_id: int = Field(gt=0)
    bicycle_id: int = Field(gt=0)
    reviewer_name: str | None = Field(None, max_length=100)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1)


class ReviewUpdate(BaseModel):
    reviewer_name: str | None = Field(None, max_length=100)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    bicycle_id: int
    reviewer_name: str | None
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime


class ReviewSummary(BaseModel):
    bicycle_id: int
    average_rating: float
    review_count: int


# ---------- API ----------
@router.post("", response_model=ReviewResponse, status_code=201)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db)):
    ensure_user_and_bicycle(db, payload.user_id, payload.bicycle_id)
    review = Review(**payload.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/bicycle/{bicycle_id}", response_model=list[ReviewResponse])
def get_reviews_by_bicycle(bicycle_id: int, db: Session = Depends(get_db)):
    query = (
        select(Review)
        .where(Review.bicycle_id == bicycle_id)
        .order_by(Review.created_at.desc(), Review.id.desc())
    )
    return db.scalars(query).all()


# คะแนนเฉลี่ยและจำนวนรีวิว คำนวณด้วย SQL (AVG, COUNT)
@router.get("/bicycle/{bicycle_id}/summary", response_model=ReviewSummary)
def get_review_summary(bicycle_id: int, db: Session = Depends(get_db)):
    average, count = db.execute(
        select(func.coalesce(func.avg(Review.rating), 0), func.count(Review.id))
        .where(Review.bicycle_id == bicycle_id)
    ).one()
    return {"bicycle_id": bicycle_id, "average_rating": round(float(average), 2), "review_count": count}


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(404, "Review not found.")
    return review


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(review_id: int, payload: ReviewUpdate, db: Session = Depends(get_db)):
    review = get_review(review_id, db)
    for field, value in payload.model_dump().items():
        setattr(review, field, value)
    db.commit()
    db.refresh(review)
    return review
