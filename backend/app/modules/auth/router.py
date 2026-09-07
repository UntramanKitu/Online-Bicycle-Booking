import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Cookie, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.unified_user import UnifiedUser

router = APIRouter(prefix="/auth", tags=["auth"])
OAUTH_STATE_COOKIE = "bikea_oauth_state"
ACCESS_TOKEN_COOKIE = "bikea_access_token"


def config(name: str) -> str:
    return os.getenv(name, "").strip()


def frontend_url(path: str = "") -> str:
    return f"{config('FRONTEND_URL') or 'http://localhost:5173'}{path}"


@router.get("/google/login")
def google_login():
    client_id = config("GOOGLE_CLIENT_ID")
    redirect_uri = config("GOOGLE_REDIRECT_URI")
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=503, detail="Google OAuth ยังไม่ได้ตั้งค่าใน backend/.env")

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
async def google_callback(code: str, state: str, oauth_state: str | None = Cookie(default=None)):
    if not oauth_state or not secrets.compare_digest(state, oauth_state):
        raise HTTPException(status_code=400, detail="OAuth state ไม่ถูกต้องหรือหมดอายุ")

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
        user = db.query(UnifiedUser).filter(UnifiedUser.google_sub == profile["sub"]).first()
        if user is None:
            user = db.query(UnifiedUser).filter(UnifiedUser.email == profile.get("email")).first()
        if user is None:
            user = UnifiedUser()
            db.add(user)
        user.google_sub = profile["sub"]
        user.email = profile.get("email")
        user.display_name = profile.get("name")
        user.avatar_url = profile.get("picture")
        db.commit()
        db.refresh(user)
        session = jwt.encode({
            "sub": str(user.id),
            "email": user.email,
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
        }, config("JWT_SECRET") or "development-only-secret", algorithm="HS256")
    finally:
        db.close()

    response = RedirectResponse(frontend_url("/"))
    response.delete_cookie(OAUTH_STATE_COOKIE)
    response.set_cookie(ACCESS_TOKEN_COOKIE, session, httponly=True, max_age=604800, samesite="lax", secure=False)
    return response


@router.get("/me")
def current_user(access_token: str | None = Cookie(default=None)):
    if not access_token:
        return {"authenticated": False, "user": None}
    try:
        payload = jwt.decode(access_token, config("JWT_SECRET") or "development-only-secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": {"id": int(payload["sub"]), "email": payload.get("email")}}


@router.post("/logout")
def logout():
    response = Response(status_code=204)
    response.delete_cookie(ACCESS_TOKEN_COOKIE)
    return response
