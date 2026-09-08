from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import PenaltyStrike, PenaltyReason, UnifiedUser
from schemas import PenaltyStrikeCreate, PenaltyStrikeUpdate, PenaltyStrikeResponse
from utils import resolve_user, get_actor, require_admin, Actor

router = APIRouter(prefix="/api/penalties", tags=["Penalties"])

MAX_POINTS = 12  # แต้มเต็ม (แนวทางเดียวกับใบขับขี่แบบตัดแต้ม)

# เงื่อนไขที่ "เพิ่ม" คะแนน (+1) — นอกนั้นทั้งหมดถือเป็นการ "หัก" คะแนน (-1)
POSITIVE_REASONS = {PenaltyReason.GOOD_BEHAVIOR, PenaltyReason.NO_VIOLATION_WEEK}


def _apply_points(user: UnifiedUser, reason: str, magnitude: int) -> None:
    """เพิ่ม/ลดแต้มผู้ใช้ตามทิศทางที่มาจาก reason เท่านั้น (ผู้เรียก API กำหนดทิศทางเองไม่ได้)"""
    delta = magnitude if reason in POSITIVE_REASONS else -magnitude
    user.points = min(MAX_POINTS, max(0, user.points + delta))


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
def create_penalty(data: PenaltyStrikeCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_actor)):
    require_admin(actor)  # ออกบทลงโทษ/ให้คะแนนเป็นสิทธิ์แอดมินเท่านั้น ผู้ใช้ทั่วไปทำเองไม่ได้
    user = resolve_user(data.user_id, db)

    valid_reasons = {r.value for r in PenaltyReason}
    if data.reason not in valid_reasons:
        raise HTTPException(status_code=422, detail=f"reason ต้องเป็นหนึ่งใน {sorted(valid_reasons)}")

    record = PenaltyStrike(**{**data.model_dump(), "user_id": user.id})
    db.add(record)
    db.flush()

    # ทิศทาง (+1/-1) มาจาก reason เท่านั้น — ผู้เรียก API กำหนดเองไม่ได้ ป้องกันการยิง
    # penalty_points ติดลบเข้ามาเพื่อแอบเพิ่มแต้มให้ตัวเอง (ดู POSITIVE_REASONS ด้านบน)
    _apply_points(user, data.reason, data.penalty_points)

    db.commit()
    db.refresh(record)
    return record


@router.put("/{penalty_id}", response_model=PenaltyStrikeResponse)
def update_penalty(penalty_id: int, data: PenaltyStrikeUpdate, db: Session = Depends(get_db), actor: Actor = Depends(get_actor)):
    require_admin(actor)
    record = db.query(PenaltyStrike).filter(PenaltyStrike.id == penalty_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Penalty not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{penalty_id}", status_code=204)
def delete_penalty(penalty_id: int, db: Session = Depends(get_db), actor: Actor = Depends(get_actor)):
    require_admin(actor)
    record = db.query(PenaltyStrike).filter(PenaltyStrike.id == penalty_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Penalty not found")
    db.delete(record)
    db.commit()


@router.post("/weekly-bonus", response_model=List[PenaltyStrikeResponse])
def apply_weekly_good_behavior_bonus(db: Session = Depends(get_db), actor: Actor = Depends(get_actor)):
    require_admin(actor)
    """
    ให้คะแนน +1 อัตโนมัติแก่ผู้ใช้ทุกคนที่ไม่มีการหักคะแนน (reason ฝั่งลบ) เกิดขึ้นเลย
    ในช่วง 7 วันที่ผ่านมา — เรียกใช้งานได้เองผ่านปุ่มในหน้าเว็บ หรือจะตั้ง cron/Task
    Scheduler ภายนอกให้ยิงมาที่ endpoint นี้สัปดาห์ละครั้งก็ได้ (ในนี้ไม่มี scheduler
    ในตัว เพราะ FastAPI เป็นแค่ API server ไม่ได้รันงาน background ตามเวลาเอง)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    negative_reasons = [r.value for r in PenaltyReason if r not in POSITIVE_REASONS]

    awarded: List[PenaltyStrike] = []
    for user in db.query(UnifiedUser).all():
        if user.points >= MAX_POINTS:
            continue  # เต็มแต้มอยู่แล้ว ไม่ต้องสร้าง record ให้เปล่าประโยชน์

        has_recent_violation = db.query(PenaltyStrike).filter(
            PenaltyStrike.user_id == user.id,
            PenaltyStrike.reason.in_(negative_reasons),
            PenaltyStrike.created_at >= cutoff,
        ).first()
        if has_recent_violation:
            continue

        already_awarded_this_week = db.query(PenaltyStrike).filter(
            PenaltyStrike.user_id == user.id,
            PenaltyStrike.reason == PenaltyReason.NO_VIOLATION_WEEK,
            PenaltyStrike.created_at >= cutoff,
        ).first()
        if already_awarded_this_week:
            continue

        record = PenaltyStrike(
            user_id=user.id,
            reason=PenaltyReason.NO_VIOLATION_WEEK,
            penalty_points=1,
            action="reward",
            description="ไม่มีการกระทำผิดครบ 7 วัน ได้รับคะแนนคืนอัตโนมัติ",
            completed=True,
        )
        db.add(record)
        _apply_points(user, record.reason, 1)
        awarded.append(record)

    db.commit()
    for record in awarded:
        db.refresh(record)
    return awarded