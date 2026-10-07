"""ทดสอบช่องว่าง requirement ที่เพิ่งทำ (M02/Confirm/Edit/Upload/Review/Reminder/งดยืม)"""
import datetime as dt
import io
import os
import sys
from pathlib import Path

import httpx
import jwt
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")  # อ่าน JWT_SECRET จาก backend/.env (ไม่ hardcode ในไฟล์)

BASE = "http://127.0.0.1:8002"
SECRET = os.getenv("JWT_SECRET") or "development-only-secret"
exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
ADMIN = jwt.encode({"sub": "3", "exp": exp}, SECRET, algorithm="HS256")
USER = jwt.encode({"sub": "2", "exp": exp}, SECRET, algorithm="HS256")

ok = fail = 0


def check(name, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"[OK] {name}")
    else:
        fail += 1
        print(f"[FAIL] {name} {extra}")


admin = httpx.Client(base_url=BASE, cookies={"bikea_access_token": ADMIN}, timeout=15)
user = httpx.Client(base_url=BASE, cookies={"bikea_access_token": USER}, timeout=15)
anon = httpx.Client(base_url=BASE, timeout=15)

# ---------- 1) Bicycle CRUD ----------
r = admin.post("/api/bicycles", json={"model": "ทดสอบ CRUD", "station": "สถานีทดสอบ", "distance": "99 ม."})
check("POST /bicycles (admin) 201 + auto code", r.status_code == 201 and r.json()["code"].startswith("BIKE-"), r.text[:200])
bike_id = r.json().get("id") if r.status_code == 201 else None

r = anon.post("/api/bicycles", json={"model": "x"})
check("POST /bicycles ไม่มี cookie -> 401", r.status_code == 401, str(r.status_code))

if bike_id:
    r = admin.put(f"/api/bicycles/{bike_id}", json={"model": "ทดสอบแก้ไขแล้ว", "battery": 77})
    check("PUT /bicycles/{id}", r.status_code == 200 and r.json()["model"] == "ทดสอบแก้ไขแล้ว", r.text[:200])
    r = admin.patch(f"/api/bicycles/{bike_id}/status", json={"is_active": False})
    check("PATCH status -> ปิดใช้ (available=false)", r.status_code == 200 and r.json()["available"] is False, r.text[:200])
    r = admin.get("/api/bicycles")
    row = next((b for b in r.json() if b["id"] == bike_id), None)
    check("GET list เห็น is_active=false", row and row["is_active"] is False, str(row))
    r = admin.delete(f"/api/bicycles/{bike_id}")
    check("DELETE /bicycles/{id}", r.status_code == 200, r.text[:200])

# ---------- 2) Upload ----------
png = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c6300010000050001")
r = user.post("/api/upload", files={"file": ("ทดสอบ.png", io.BytesIO(png), "image/png")})
check("POST /upload 200 + url", r.status_code in (200, 201) and r.json()["url"].startswith("/api/uploads/"), r.text[:200])
upload_url = r.json().get("url") if r.status_code in (200, 201) else None
if upload_url:
    r = anon.get(upload_url)
    check("GET static /api/uploads/...", r.status_code == 200 and r.content[:4] == b"\x89PNG", str(r.status_code))
r = user.post("/api/upload", files={"file": ("x.txt", io.BytesIO(b"hi"), "text/plain")})
check("upload ไฟล์ไม่ใช่รูป -> 400", r.status_code == 400, str(r.status_code))

# ---------- 3) Booking: สร้าง / เลื่อนเวลา / conflict / confirm ----------
start = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0) + dt.timedelta(days=2, hours=3)
end = start + dt.timedelta(hours=1)
booking_id = None
used_bike = None
for bike in range(1, 9):
    r = user.post("/api/bookings", json={
        "user_id": 2, "bicycle_id": bike, "booking_type": "advance_reservation",
        "start_time": start.isoformat(), "end_time": end.isoformat(),
        "pickup_location": "สถานีประตู 1", "note": "ทดสอบเลื่อนเวลา",
    })
    if r.status_code == 201:
        booking_id = r.json()["id"]
        used_bike = bike
        break
check("POST /bookings 201", booking_id is not None, r.text[:200])

if booking_id:
    # 3a) เลื่อนเวลา (PUT)
    new_start = start + dt.timedelta(hours=2)
    new_end = new_start + dt.timedelta(hours=1)
    r = user.put(f"/api/bookings/{booking_id}", json={"start_time": new_start.isoformat(), "end_time": new_end.isoformat()})
    check("PUT /bookings เลื่อนเวลา 200", r.status_code == 200 and r.json()["start_time"][:16] == new_start.isoformat()[:16], r.text[:200])

    # 3b) conflict — จองซ้อนเวลาเดียวกับ bike เดิม
    r2 = user.post("/api/bookings", json={
        "user_id": 2, "bicycle_id": used_bike, "booking_type": "advance_reservation",
        "start_time": (new_start + dt.timedelta(minutes=10)).isoformat(),
        "end_time": (new_start + dt.timedelta(minutes=50)).isoformat(),
    })
    check("จองซ้ำช่วงเวลาเดียวกัน -> 409", r2.status_code == 409, str(r2.status_code))

    # 3c) confirm โดยแอดมิน
    r = admin.post(f"/api/bookings/{booking_id}/confirm", params={"user_id": 3})
    check("POST /bookings/confirm (admin) -> confirmed", r.status_code == 200 and r.json()["status"] == "confirmed", r.text[:200])
    r = user.get("/api/notifications/user/2")
    has_note = any("ยืนยัน" in n["title"] for n in r.json())
    check("confirm สร้างแจ้งเตือนให้เจ้าของจอง", has_note)

    # 3d) confirm ซ้ำ -> 400 (ไม่ใช่ pending)
    r = admin.post(f"/api/bookings/{booking_id}/confirm", params={"user_id": 3})
    check("confirm ซ้ำ -> 400", r.status_code == 400, str(r.status_code))

# ---------- 4) งดยืมตามแต้ม (M12) ----------
os.system('docker exec bikea_db psql -U bikea -d bikea -c "UPDATE accounts_unifieduser SET points=5 WHERE id=2" > nul')
r = user.post("/api/bookings", json={
    "user_id": 2, "bicycle_id": 1, "booking_type": "advance_reservation",
    "start_time": (start + dt.timedelta(days=1)).isoformat(),
    "end_time": (start + dt.timedelta(days=1, hours=1)).isoformat(),
})
check("แต้ม 5 -> จองไม่ได้ 403", r.status_code == 403, f"{r.status_code} {r.text[:150]}")
if booking_id:
    r = user.post(f"/api/bookings/{booking_id}/borrow", params={"user_id": 2})
    check("แต้ม 5 -> borrow ไม่ได้ 403", r.status_code == 403, f"{r.status_code} {r.text[:150]}")
os.system('docker exec bikea_db psql -U bikea -d bikea -c "UPDATE accounts_unifieduser SET points=12 WHERE id=2" > nul')
r = user.post("/api/bookings", json={
    "user_id": 2, "bicycle_id": 1, "booking_type": "advance_reservation",
    "start_time": (start + dt.timedelta(days=1)).isoformat(),
    "end_time": (start + dt.timedelta(days=1, hours=1)).isoformat(),
})
check("แต้ม 12 -> จองได้ 201", r.status_code == 201, f"{r.status_code} {r.text[:150]}")
if r.status_code == 201:
    admin.delete(f"/api/bookings/{r.json()['id']}")

# ---------- 5) Review delete ----------
r = user.post("/api/reviews", json={"user_id": 2, "bicycle_id": 7, "rating": 4.5, "comment": "ทดสอบลบรีวิว"})
check("POST /reviews 201", r.status_code == 201, r.text[:200])
review_id = r.json().get("id") if r.status_code == 201 else None
if review_id:
    r = user.delete(f"/api/reviews/{review_id}", params={"user_id": 2})
    check("DELETE review (เจ้าของ)", r.status_code == 200 and r.json()["deleted"] == 1, r.text[:200])
    r = user.post("/api/reviews", json={"user_id": 2, "bicycle_id": 7, "rating": 3, "comment": "แอดมินจะลบ"})
    rid2 = r.json()["id"]
    r = admin.delete(f"/api/reviews/{rid2}", params={"user_id": 3})
    check("DELETE review (แอดมิน)", r.status_code == 200, r.text[:200])

# ---------- 6) Maintenance + images ----------
payload = {"bicycle_id": 7, "reported_by": 2, "issue_type": "ยางแบน", "description": "ทดสอบรูปแนบ"}
if upload_url:
    payload["images"] = [upload_url]
r = user.post("/api/maintenance-reports", json=payload)
expected = [upload_url] if upload_url else []
check("POST /maintenance-reports + images", r.status_code == 201 and (r.json().get("images") or []) == expected, r.text[:250])
report_id = r.json().get("id") if r.status_code == 201 else None
if report_id:
    r = user.get("/api/maintenance-reports/user/2")
    row = next((x for x in r.json() if x["id"] == report_id), None)
    check("GET reports มี images กลับมา", row is not None and (row.get("images") or []) == expected, str(row and row.get("images")))

# ---------- 7) Reminders (_tick โดยตรง) ----------
from app.modules.nathida.reminders import _tick  # noqa: E402

rem_start = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0) + dt.timedelta(minutes=10)
rem_booking = None
for bike in range(1, 9):
    r = user.post("/api/bookings", json={
        "user_id": 2, "bicycle_id": bike, "booking_type": "advance_reservation",
        "start_time": rem_start.isoformat(), "end_time": (rem_start + dt.timedelta(minutes=30)).isoformat(),
    })
    if r.status_code == 201:
        rem_booking = r.json()["id"]
        break
check("จองสำหรับทดสอบ reminder", rem_booking is not None, r.text[:200])
if rem_booking:
    before = len(user.get("/api/notifications/user/2").json())
    _tick()
    after_list = user.get("/api/notifications/user/2").json()
    reminded = [n for n in after_list if "ใกล้ถึงเวลาไปรับรถ" in n["title"]]
    check("_tick สร้างแจ้งเตือนเตือนล่วงหน้า", len(after_list) > before and reminded, f"before={before} after={len(after_list)}")
    _tick()
    again = user.get("/api/notifications/user/2").json()
    check("_tick ซ้ำไม่ส่งซ้ำ", len(again) == len(after_list), f"{len(after_list)} vs {len(again)}")
    admin.delete(f"/api/bookings/{rem_booking}")

# cleanup
if booking_id:
    admin.delete(f"/api/bookings/{booking_id}")
if report_id:
    os.system(f'docker exec bikea_db psql -U bikea -d bikea -c "DELETE FROM maintenance_reports WHERE id={report_id}" > nul')
os.system('docker exec bikea_db psql -U bikea -d bikea -c "DELETE FROM notifications WHERE title IN (\'การจองได้รับการยืนยัน\',\'ใกล้ถึงเวลาไปรับรถ\',\'เลยกำหนดคืนรถ\')" > nul')

print(f"\n=== PASS {ok} / FAIL {fail} ===")
sys.exit(1 if fail else 0)
