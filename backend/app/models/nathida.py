"""ตาราง M13-M15 ของ Nathida (Notification / Maintenance / Review)

FK ชี้ไปตารางจริง — ไม่สร้างตาราง stub users/bicycles แยก:
- user FK -> accounts_unifieduser.id (BigInteger, ตารางของ Django Monolith — ฝั่งนี้อ่านอย่างเดียว)
- bicycle FK -> bicycle.id (Integer, ตารางฝั่งเรา)

ถ้า user/bike ไม่มี ให้ API ตอบ 404 (ไม่มีการสร้างแถว stub อัตโนมัติ)
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# M13 Notification
class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("accounts_unifieduser.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# M14 Maintenance Report
class MaintenanceReport(Base):
    __tablename__ = "maintenance_reports"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, index=True)
    bicycle_id: Mapped[int] = mapped_column(ForeignKey("bicycle.id"), index=True)
    reported_by: Mapped[int] = mapped_column(ForeignKey("accounts_unifieduser.id"), index=True)
    issue_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    resolved_note: Mapped[str | None] = mapped_column(Text)
    # รูปภาพแนบตอนแจ้งซ่อม (เก็บ JSON array ของ URL เช่น ["/api/uploads/xxx.jpg"])
    images: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# M15 Feedback & Rating
class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("accounts_unifieduser.id"), index=True)
    bicycle_id: Mapped[int] = mapped_column(ForeignKey("bicycle.id"), index=True)
    reviewer_name: Mapped[str | None] = mapped_column(String(100))
    # เก็บคะแนนแบบ float (1.0-5.0 กดครึ่งดาวได้) — Postgres ใช้ DOUBLE PRECISION
    rating: Mapped[float] = mapped_column(DOUBLE_PRECISION)
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# กัน flake: BigInteger ถูกใช้ผ่าน ForeignKey string เท่านั้น แต่ import ไว้เพื่อบอก type ชัดเจน
__all__ = ["Notification", "MaintenanceReport", "Review", "BigInteger"]
