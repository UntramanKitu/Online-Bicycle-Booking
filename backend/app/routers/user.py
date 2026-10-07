from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.unified_user import UnifiedUser
from app.modules.auth.deps import require_admin
from app.modules.auth.roles import resolve_role
from app.schemas.user import UserResponse


class UpdateRoleRequest(BaseModel):
    role: str  # 'admin' หรือ 'user'

router = APIRouter()


def _db_user_to_response(user: UnifiedUser) -> dict:
    """แปลงแถว accounts_unifieduser (คอลัมน์ Django AbstractUser) ให้ตรง UserResponse

    ตารางจริงไม่มีคอลัมน์ student_id / faculty / department / role / status
    เติมค่า default ให้ frontend แสดงผลได้โดยไม่ต้องแก้ shape เดิม
    """
    full_name = (user.full_name or "").strip() or user.username
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name,
        "student_id": None,
        "faculty": None,
        "department": None,
        "role": resolve_role(user),
        "status": "active" if user.is_active else "inactive",
        "points": user.points,
    }



@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """รายชื่อผู้ใช้ — ผู้ใช้ตัวจริงจาก Google login ทั้งหมด (ไม่มี mock)"""
    rows = (
        db.query(UnifiedUser)
        .filter(UnifiedUser.is_active == True)  # noqa: E712 — SQLAlchemy ต้องใช้ == กับคอลัมน์
        .order_by(UnifiedUser.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_db_user_to_response(u) for u in rows]


@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UnifiedUser).filter(UnifiedUser.id == user_id).first()
    if user is not None:
        return _db_user_to_response(user)
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/admin/users", response_model=List[UserResponse])
def admin_list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _admin: UnifiedUser = Depends(require_admin),
):
    """[แอดมินเท่านั้น] รายชื่อผู้ใช้ทุกคนรวมทั้ง inactive"""
    rows = (
        db.query(UnifiedUser)
        .order_by(UnifiedUser.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_db_user_to_response(u) for u in rows]


@router.patch("/admin/users/{user_id}/role", response_model=UserResponse)
def admin_update_role(
    user_id: int,
    body: UpdateRoleRequest,
    db: Session = Depends(get_db),
    _admin: UnifiedUser = Depends(require_admin),
):
    """[แอดมินเท่านั้น] เปลี่ยน role ผู้ใช้ — 'admin' ตั้ง is_staff=True, 'user' ตั้ง is_staff=False"""
    if body.role not in {"admin", "user"}:
        raise HTTPException(status_code=422, detail="role ต้องเป็น 'admin' หรือ 'user' เท่านั้น")
    user = db.query(UnifiedUser).filter(UnifiedUser.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_staff = body.role == "admin"
    db.commit()
    db.refresh(user)
    return _db_user_to_response(user)
