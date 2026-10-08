import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlsplit

import httpx
import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.unified_user import UnifiedUser
from app.modules.auth.roles import resolve_role

router = APIRouter(prefix="/auth", tags=["auth"])
OAUTH_STATE_COOKIE = "bikea_oauth_state"
ACCESS_TOKEN_COOKIE = "bikea_access_token"


def config(name: str) -> str:
    return os.getenv(name, "").strip()


def user_provisioning_enabled() -> bool:
    """ตาราง accounts_unifieduser เป็นของฝั่ง Django Monolith — ฝั่งนี้อ่านอย่างเดียวเป็นค่าเริ่มต้น

    ถ้าเปิด true จะ INSERT user ใหม่ลงตาราง (ใช้ตอน demo ที่ยังไม่มี Django)
    แต่เสี่ยงชนกับฝั่ง Django เมื่อระบบรวมกันแล้ว
    """
    return config("AUTH_USER_PROVISIONING").lower() in {"1", "true", "yes", "on"}


def _unique_username(db, email: str) -> str:
    """สร้าง username ที่ไม่ซ้ำจากอีเมล (username เป็น UNIQUE ใน AbstractUser)

    ใช้ส่วนก่อน @ เป็นฐาน แล้วต่อเลขท้ายถ้าซ้ำ
    """
    base = re.sub(r"[^a-z0-9._-]+", "_", email.split("@")[0].lower()).strip("_") or "user"
    base = base[:140]
    candidate = base
    suffix = 1
    while db.query(UnifiedUser).filter(UnifiedUser.username == candidate).first() is not None:
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


def frontend_url(path: str = "") -> str:
    return f"{config('FRONTEND_URL') or 'http://localhost:5173'}{path}"


@router.get("/google/login")
def google_login(request: Request):
    client_id = config("GOOGLE_CLIENT_ID")
    redirect_uri = config("GOOGLE_REDIRECT_URI")
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=503, detail="Google OAuth ยังไม่ได้ตั้งค่าใน backend/.env")

    # Cookie ผูกกับ host (localhost กับ 127.0.0.1 ถือเป็นคนละ host)
    # ถ้าเข้า login ผ่าน host อื่นที่ไม่ใช่ host ของ redirect_uri cookie state จะไม่ถูกส่งกลับมาที่ callback
    # จึง redirect ให้เข้าผ่าน host เดียวกับ redirect_uri ก่อน
    callback = urlsplit(redirect_uri)
    request_host = request.headers.get("host")
    if request_host and request_host != callback.netloc:
        return RedirectResponse(f"{callback.scheme}://{callback.netloc}{request.url.path}")

    state = secrets.token_urlsafe(32)
    query = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    })
    response = RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")
    response.set_cookie(OAUTH_STATE_COOKIE, state, httponly=True, max_age=600, samesite="lax")
    return response


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    oauth_state: str | None = Cookie(default=None, alias=OAUTH_STATE_COOKIE),
):
    # Google จะ redirect กลับมาพร้อม code/state เสมอ ถ้าพารามิเตอร์ขาดหาย
    # (เปิด/รีเฟรช URL callback ตรง ๆ) หรือผู้ใช้กดยกเลิกที่หน้า Google (error=access_denied)
    # ให้กลับไปหน้า login พร้อมข้อความแทนการตอบ JSON error
    if error or not code or not state or not oauth_state or not secrets.compare_digest(state, oauth_state):
        return RedirectResponse(f"{frontend_url('/login')}?error=oauth_failed")

    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": config("GOOGLE_CLIENT_ID"),
            "client_secret": config("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": config("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        })
        if token_response.is_error:
            raise HTTPException(status_code=400, detail="แลก Google authorization code ไม่สำเร็จ")
        access_token = token_response.json().get("access_token")
        profile_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_response.is_error:
            raise HTTPException(status_code=400, detail="อ่านข้อมูลบัญชี Google ไม่สำเร็จ")
        profile = profile_response.json()

    db = SessionLocal()
    try:
        email = (profile.get("email") or "").strip()
        if not email:
            # สโคปขอลอง scope "email" อยู่แล้ว — ถ้าไม่มีคือยิงกับ Google ผิดหรือผู้ใช้ปฏิเสธ
            raise HTTPException(status_code=400, detail="บัญชี Google ไม่ได้ให้อีเมล")

        # ตารางนี้เป็นของ Django (AbstractUser) จึงไม่มีคอลัมน์ google_sub
        # จึงจับคู่ด้วย email ซึ่งเป็นคอลัมน์ที่สองฝั่งมีตรงกัน
        user = db.query(UnifiedUser).filter(UnifiedUser.email == email).first()
        if user is None and user_provisioning_enabled():
            user = UnifiedUser(
                username=_unique_username(db, email),
                email=email,
                first_name=(profile.get("name") or ""),
                last_name="",
                password="",  # รหัสผ่านว่าง = บัญชี OAuth ล็อกอินด้วยรหัสผ่านไม่ได้
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        if user is None:
            # บัญชียังไม่มี — ปล่อยให้ฝั่ง Django เป็นเจ้าของการสมัครสมาชิก
            response = RedirectResponse(f"{frontend_url('/login')}?error=user_not_registered")
            response.delete_cookie(OAUTH_STATE_COOKIE)
            return response
        session = jwt.encode({
            "sub": str(user.id),
            "email": user.email,
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
        }, config("JWT_SECRET") or "development-only-secret", algorithm="HS256")
        # เก็บ role ก่อนปิด db — แอดมินเข้าหน้า /admin ตรง ๆ ส่วนผู้ใช้ทั่วไปไปหน้าหลัก
        role = resolve_role(user)
    finally:
        db.close()

    landing = "/admin" if role == "admin" else "/"
    response = RedirectResponse(frontend_url(landing))
    response.delete_cookie(OAUTH_STATE_COOKIE)
    response.set_cookie(ACCESS_TOKEN_COOKIE, session, httponly=True, max_age=604800, samesite="lax", secure=False)
    return response


class ProfileUpdate(BaseModel):
    """แก้ไขชื่อโปรไฟล์จากหน้า /profile — ส่งเฉพาะช่องที่อยากแก้"""

    first_name: str | None = Field(None, max_length=150)
    last_name: str | None = Field(None, max_length=150)


def _user_from_cookie(
    access_token: str | None,
    db: Session,
) -> UnifiedUser | None:
    """อ่าน cookie bikea_access_token → คืน user ที่ยัง active (ไม่พบ/หมดอายุ = None)"""
    if not access_token:
        return None
    try:
        payload = jwt.decode(access_token, config("JWT_SECRET") or "development-only-secret", algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
    user = db.get(UnifiedUser, user_id)
    if user is None or not user.is_active:
        return None
    return user


def _me_user_payload(user: UnifiedUser) -> dict:
    """รูปข้อมูลผู้ใช้ที่ /auth/me คืนให้ frontend (ใช้ซ้ำทั้ง GET และ PATCH)"""
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name,
        "role": resolve_role(user),
        "status": "active" if user.is_active else "inactive",
        "points": user.points,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
    }


@router.get("/me")
def current_user(
    access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    db: Session = Depends(get_db),
):
    user = _user_from_cookie(access_token, db)
    if user is None:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": _me_user_payload(user)}


@router.patch("/me")
def update_profile(
    payload: ProfileUpdate,
    access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    db: Session = Depends(get_db),
):
    """แก้ชื่อ/นามสกุลของตัวเองจากหน้าโปรไฟล์ — ต้องล็อกอิน (cookie) เท่านั้น"""
    user = _user_from_cookie(access_token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบก่อนแก้ไขโปรไฟล์")
    if payload.first_name is not None:
        user.first_name = payload.first_name.strip()
    if payload.last_name is not None:
        user.last_name = payload.last_name.strip()
    db.commit()
    db.refresh(user)
    return {"authenticated": True, "user": _me_user_payload(user)}


@router.post("/logout")
def logout():
    response = Response(status_code=204)
    response.delete_cookie(ACCESS_TOKEN_COOKIE)
    return response
