"""ตารางในฐานข้อมูลทั้งหมด (SQLAlchemy models)

users และ bicycles เป็นตารางชั่วคราว (stub) ไว้ให้ foreign key ชี้ถึงได้
จนกว่าโมดูล user/bicycle จริงของทีมจะเชื่อมเข้ามา
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Identity, Integer, String, Text, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Bicycle(Base):
    __tablename__ = "bicycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# M13 Notification
class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# M14 Maintenance Report
class MaintenanceReport(Base):
    __tablename__ = "maintenance_reports"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, index=True)
    bicycle_id: Mapped[int] = mapped_column(ForeignKey("bicycles.id"), index=True)
    reported_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    issue_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    resolved_note: Mapped[str | None] = mapped_column(Text)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# M15 Feedback & Rating
class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    bicycle_id: Mapped[int] = mapped_column(ForeignKey("bicycles.id"), index=True)
    reviewer_name: Mapped[str | None] = mapped_column(String(100))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# สร้างแถว user/bicycle ชั่วคราวถ้ายังไม่มี เพื่อให้ foreign key ผ่าน
def ensure_user_and_bicycle(db: Session, user_id: int, bicycle_id: int) -> None:
    if db.get(User, user_id) is None:
        db.add(User(id=user_id, full_name=f"User {user_id}",
                    email=f"user{user_id}@example.local", password="placeholder"))
    if db.get(Bicycle, bicycle_id) is None:
        db.add(Bicycle(id=bicycle_id, name=f"Bicycle {bicycle_id}"))
    db.flush()
