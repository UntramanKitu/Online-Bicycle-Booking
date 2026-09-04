"""ตรวจสอบว่าระบบเชื่อมต่อ PostgreSQL ท้องถิ่น (Docker port 5434) โดยไม่พึ่ง Supabase"""
import sys
sys.path.insert(0, ".")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fastapi.testclient import TestClient
from sqlalchemy import text

# ชี้ให้เห็นว่า engine ใช้ .env ใหม่ (local) — ตรวจ URL ไม่ให้มี supabase
from app.database import engine, SessionLocal
import app.database as database

print("DATABASE_URL:", database.DATABASE_URL.replace(database.DATABASE_URL.split(":")[1].strip("/"), "***") if ":" in database.DATABASE_URL else database.DATABASE_URL)
assert "supabase" not in database.DATABASE_URL.lower(), "ยังมี supabase อยู่!"

# 1) เชื่อมต่อ + ทดสอบ simple query
with engine.connect() as conn:
    v = conn.execute(text("SELECT current_database(), current_user, version()")).fetchone()
    print("DB:", v[0], "| user:", v[1])
    print("PG:", v[2].split(" on ")[0])

# 2) สร้างตารางทั้งหมด (จากโมเดล)
from app.models import booking, group_ride, bicycle, unified_user, students, staff_officer
from app.database import Base
Base.metadata.create_all(bind=engine)
print("สร้างตารางแล้ว:", sorted(Base.metadata.tables.keys()))

# 3) Seed ข้อมูลของชัยอนันต์
from app.seed.seed_bookings import main as seed_main
seed_main()

# 4) ทดสอบ API ผ่าน FastAPI app จริง (ใช้ main app)
from app.main import app as real_app
client = TestClient(real_app)

r = client.get("/api/group-rides")
print("GET /api/group-rides:", r.status_code, "| จำนวน:", len(r.json()))
assert r.status_code == 200 and len(r.json()) >= 3

r = client.get("/api/bookings")
print("GET /api/bookings:", r.status_code if hasattr else r.status_code, "| จำนวน:", len(r.json()))
assert r.status_code == 200 and len(r.json()) >= 5

r = client.get("/api/tickets" if False else "/api/tickets")
print("GET /api/tickets:", r.status_code, "| จำนวน:", len(r.json()))
assert r.status_code == 200 and len(r.json()) >= 5

# 5) ทดสอบ Availability (จองซ้อนทับต้อง 409)
r = client.post("/api/bookings", json={
    "user_id": 9, "bicycle_id": 1, "booking_type": "walk_in",
    "start_time": "2026-08-10T09:30:00", "end_time": "2026-08-10T10:30:00",
})
print("POST /api/bookings ซ้อน →", "409 (ถูก)" if r.status_code == 409 else r.content)
assert r.status_code == 409

print("\n✅ ทุกอย่างทำงานกับ PostgreSQL ท้องถิ่น (ไม่มี Supabase)")