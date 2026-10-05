"""ทดสอบยืนยัน OAuth state flow ทั้งหมด"""
import os

os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_REDIRECT_URI"] = "http://127.0.0.1:8002/api/auth/google/callback"

import jwt as pyjwt
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.auth.router import ACCESS_TOKEN_COOKIE, OAUTH_STATE_COOKIE, router

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app, raise_server_exceptions=False, follow_redirects=False)

failures = []

# 1) เข้า login ผ่าน host ที่ไม่ตรงกับ redirect_uri -> ต้อง redirect ไป host ของ redirect_uri ก่อน
r = client.get("/api/auth/google/login")  # default Host = testserver
loc = r.headers.get("location", "")
print(f"[1] login via mismatched host -> {r.status_code} {loc}")
if r.status_code != 307 or "127.0.0.1:8002" not in loc:
    failures.append("host mismatch ต้อง redirect ไป host ของ redirect_uri")

# 2) เข้า login ผ่าน host ที่ตรงกัน -> redirect ไป Google พร้อม set cookie
r = client.get("/api/auth/google/login", headers={"Host": "127.0.0.1:8002"})
loc = r.headers.get("location", "")
set_cookie = r.headers.get("set-cookie", "")
print(f"[2] login via matching host -> {r.status_code} to google={loc.startswith('https://accounts.google.com')}, cookie={OAUTH_STATE_COOKIE in set_cookie}")
if r.status_code != 307 or not loc.startswith("https://accounts.google.com") or OAUTH_STATE_COOKIE not in set_cookie:
    failures.append("login ปกติต้อง redirect ไป Google และ set cookie bikea_oauth_state")

# 3) callback พร้อม cookie ถูกต้อง -> ต้องผ่าน state check (fail ที่ Google token exchange แทน)
state = set_cookie.split(f"{OAUTH_STATE_COOKIE}=")[1].split(";")[0]
r = client.get(
    "/api/auth/google/callback",
    params={"code": "fake-code", "state": state},
    cookies={OAUTH_STATE_COOKIE: state},
    headers={"Host": "127.0.0.1:8002"},
)
body = r.text
state_rejected = "oauth_failed" in r.headers.get("location", "")
print(f"[3] callback with correct cookie -> {r.status_code} state_rejected={state_rejected} body={body[:80]!r}")
if state_rejected:
    failures.append("cookie alias ยังไม่ถูกอ่าน (state check fail ทั้งที่ cookie ถูกส่ง)")
elif r.status_code != 400 or "authorization code" not in body:
    failures.append("state ผ่านแล้ว แต่ไม่ได้ fail ที่การแลก code กับ Google ตามที่คาด")

# 4) callback โดยไม่ส่ง cookie -> ต้องถูกปฏิเสธด้วย redirect กลับหน้า login
client.cookies.clear()
r = client.get(
    "/api/auth/google/callback",
    params={"code": "fake-code", "state": state},
    headers={"Host": "127.0.0.1:8002"},
)
loc = r.headers.get("location", "")
print(f"[4] callback without cookie -> {r.status_code} {loc!r}")
if not loc.endswith("/login?error=oauth_failed"):
    failures.append("ไม่มี cookie ต้องถูกปฏิเสธ (redirect กลับ /login?error=oauth_failed)")

# 5) /me ต้องอ่าน cookie ชื่อ bikea_access_token
token = pyjwt.encode({"sub": "1", "email": "t@e.com"}, os.environ.get("JWT_SECRET", "") or "development-only-secret", algorithm="HS256")
r = client.get("/api/auth/me", cookies={ACCESS_TOKEN_COOKIE: token})
print(f"[5] /me with correct cookie -> {r.status_code} {r.json()}")
if not r.json().get("authenticated"):
    failures.append("/me ยังอ่าน cookie ผิดชื่อ")

if failures:
    print("\nFAILED:")
    for f in failures:
        print(" -", f)
    raise SystemExit(1)
print("\nALL CHECKS PASSED")
