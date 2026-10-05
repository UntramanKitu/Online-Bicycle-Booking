"""M13 Notification: สร้าง / ดู / กดอ่านแจ้งเตือน"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification, User

router = APIRouter(prefix="/api/notifications", tags=["Notification"])


# ---------- รูปแบบข้อมูลเข้า/ออก ----------
class NotificationCreate(BaseModel):
    user_id: int = Field(gt=0)
    title: str
    message: str


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime


# ---------- API ----------
@router.post("", response_model=NotificationResponse, status_code=201)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    if db.get(User, payload.user_id) is None:
        raise HTTPException(404, "User not found.")
    notification = Notification(**payload.model_dump(), is_read=False)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.get("/user/{user_id}", response_model=list[NotificationResponse])
def get_notifications_by_user(user_id: int, db: Session = Depends(get_db)):
    query = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    )
    return db.scalars(query).all()


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(404, "Notification not found.")
    return notification


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    notification = get_notification(notification_id, db)
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
