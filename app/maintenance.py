"""M14 Maintenance Report: แจ้งซ่อมจักรยาน

ผู้ใช้: แจ้งซ่อม / ดูรายการของตัวเอง / แก้ไขได้เฉพาะตอนยัง pending
แอดมิน: ดูทั้งหมด / เปลี่ยนสถานะ
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MaintenanceReport, ensure_user_and_bicycle

router = APIRouter(prefix="/api/maintenance-reports")
USER = ["Maintenance Report"]
ADMIN = ["Maintenance Report (Admin)"]

STATUSES = ("pending", "in_progress", "resolved", "cancelled")
CLOSED_STATUSES = ("resolved", "cancelled")


# ---------- รูปแบบข้อมูลเข้า/ออก ----------
class ReportCreate(BaseModel):
    bicycle_id: int = Field(gt=0)
    reported_by: int = Field(gt=0)
    issue_type: str = Field(max_length=50)
    description: str = Field(min_length=1)


class ReportUpdate(BaseModel):
    issue_type: str | None = Field(None, max_length=50)
    description: str | None = Field(None, min_length=1)


class StatusUpdate(BaseModel):
    status: str
    resolved_note: str | None = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bicycle_id: int
    reported_by: int
    issue_type: str
    description: str
    status: str
    resolved_note: str | None
    reported_at: datetime
    resolved_at: datetime | None


def get_report_or_404(db: Session, report_id: int) -> MaintenanceReport:
    report = db.get(MaintenanceReport, report_id)
    if report is None:
        raise HTTPException(404, "Maintenance report not found.")
    return report


# ---------- API ฝั่งผู้ใช้ ----------
@router.post("", response_model=ReportResponse, status_code=201, tags=USER)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    ensure_user_and_bicycle(db, payload.reported_by, payload.bicycle_id)
    report = MaintenanceReport(**payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/user/{user_id}", response_model=list[ReportResponse], tags=USER)
def get_reports_by_user(user_id: int, db: Session = Depends(get_db)):
    query = (
        select(MaintenanceReport)
        .where(MaintenanceReport.reported_by == user_id)
        .order_by(MaintenanceReport.reported_at.desc(), MaintenanceReport.id.desc())
    )
    return db.scalars(query).all()


@router.put("/{report_id}", response_model=ReportResponse, tags=USER)
def update_report(report_id: int, payload: ReportUpdate, db: Session = Depends(get_db)):
    report = get_report_or_404(db, report_id)
    if report.status != "pending":
        raise HTTPException(409, "Only reports that are still pending can be edited.")
    # แก้เฉพาะช่องที่ส่งมา
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    db.commit()
    db.refresh(report)
    return report


# ---------- API ฝั่งแอดมิน ----------
@router.get("", response_model=list[ReportResponse], tags=ADMIN)
def get_all_reports(status: str | None = None, db: Session = Depends(get_db)):
    query = select(MaintenanceReport)
    if status:
        query = query.where(MaintenanceReport.status == status)
    query = query.order_by(MaintenanceReport.reported_at.desc(), MaintenanceReport.id.desc())
    return db.scalars(query).all()


@router.put("/{report_id}/status", response_model=ReportResponse, tags=ADMIN)
def update_status(report_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in STATUSES:
        raise HTTPException(400, f"Status must be one of {', '.join(STATUSES)}.")
    report = get_report_or_404(db, report_id)
    report.status = payload.status
    report.resolved_note = payload.resolved_note
    # บันทึกเวลาปิดงานเมื่อเป็น resolved/cancelled
    report.resolved_at = datetime.now(timezone.utc) if payload.status in CLOSED_STATUSES else None
    db.commit()
    db.refresh(report)
    return report
