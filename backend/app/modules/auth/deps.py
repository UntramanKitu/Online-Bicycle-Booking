"""Dependencies ตรวจสิทธิ์จาก cookie ของ Google login (bikea_access_token)

ใช้คุ้มกัน endpoint ที่อนุญาตเฉพาะแอดมิน (เช่น ดูแจ้งเตือน/ข้อมูลของทุกคน)
ส่วน endpoint เดิมที่รับ user_id จาก client ยังไม่เปลี่ยนพฤติกรรม (นอก scope)
"""

import os
from typing import Optional

import jwt
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.unified_user import UnifiedUser
from app.modules.auth.roles import resolve_role

ACCESS_TOKEN_COOKIE = "bikea_access_token"


def get_current_user(
    access_token: Optional[str] = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    db: Session = Depends(get_db),
) -> Optional[UnifiedUser]:
    """อ่าน user จาก cookie JWT — คืน None ถ้าไม่ได้ล็อกอิน/токЕНหมดอายุ/บัญชีถูกปิด"""
    if not access_token:
        return None
    try:
        payload = jwt.decode(
            access_token,
            os.getenv("JWT_SECRET") or "development-only-secret",
            algorithms=["HS256"],
        )
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
    user = db.get(UnifiedUser, user_id)
    if user is None or not user.is_active:
        return None
    return user


def require_admin(
    access_token: Optional[str] = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    db: Session = Depends(get_db),
) -> UnifiedUser:
    """สำหรับ endpoint ที่เฉพาะแอดมิน — 401 ถ้าไม่ได้ล็อกอิน, 403 ถ้าไม่ใช่แอดมิน"""
    user = get_current_user(access_token=access_token, db=db)
    if user is None:
        raise HTTPException(status_code=401, detail="ต้องเข้าสู่ระบบก่อนใช้งาน")
    if resolve_role(user) != "admin":
        raise HTTPException(status_code=403, detail="เฉพาะแอดมินเท่านั้นที่ดูข้อมูลนี้ได้")
    return user
