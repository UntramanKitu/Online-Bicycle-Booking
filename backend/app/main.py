import os
import sys

from fastapi import FastAPI
from sqlalchemy import text

# กัน App crash ตอน print ภาษาไทย/emoji ใน console/pipe ที่ encoding ไม่ใช่ UTF-8 (เช่น Windows cp874)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.routers import bicycle, user, uploads
from app.modules.eakapol import favorites, lost_items, penalties
from app.modules.auth import router as auth
from app.modules.chaianan.reservation_booking import router as reservation_booking
from app.modules.chaianan.group_ride_bookings import router as group_ride
from app.modules.chaianan.support_tickets import router as support_ticket
from app.modules.nathida import maintenance as nathida_maintenance
from app.modules.nathida import notification as nathida_notification
from app.modules.nathida import reminders as nathida_reminders
from app.modules.nathida import review as nathida_review
from app.models.bicycle import Bicycle
from app.models.unified_user import UnifiedUser
from app.models.booking import ReservationBooking, SupportTicket
from app.models.group_ride import GroupRide, GroupRideMember
from app.models.nathida import MaintenanceReport, Notification, Review
from app.models.eakapol import Favorite, PenaltyStrike, LostItem
from app.seed.seed_bookings import main as seed_main
from app.seed.seed_bicycles import main as seed_bicycles

app = FastAPI()

# Include routers
app.include_router(reservation_booking.router, prefix="/api", tags=["reservation-booking"])
app.include_router(support_ticket.router, prefix="/api", tags=["support-ticket"])
app.include_router(group_ride.router, prefix="/api", tags=["group-ride"])
app.include_router(favorites.router)
app.include_router(lost_items.router)
app.include_router(penalties.router)
app.include_router(bicycle.router, prefix="/api", tags=["bicycle"])
app.include_router(user.router, prefix="/api", tags=["users"])
app.include_router(uploads.router, prefix="/api", tags=["upload"])
app.include_router(auth.router, prefix="/api")
app.include_router(nathida_notification.router)
app.include_router(nathida_maintenance.router)
app.include_router(nathida_review.router)

# เสิร์ฟรูปที่อัปโหลด (แจ้งซ่อม) — mount ใต้ /api เพื่อให้ผ่าน vite proxy เหมือน endpoint อื่น
uploads.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(uploads.UPLOAD_DIR)), name="uploads")

# สร้างตาราง (ทำซ้ำได้ / idempotent — ใช้ checkfirst ของ SQLAlchemy)
TABLES = [
    ReservationBooking.__table__,
    SupportTicket.__table__,
    GroupRide.__table__,
    GroupRideMember.__table__,
    Bicycle.__table__,
    UnifiedUser.__table__,
    Notification.__table__,
    MaintenanceReport.__table__,
    Review.__table__,
    Favorite.__table__,
    PenaltyStrike.__table__,
    LostItem.__table__,
]


# CORS: รองรับทั้ง localhost และ 127.0.0.1 (เบราว์เซอร์ถือเป็น origin คนละตัว)
# รวมถึง origin จาก FRONTEND_URL และ CORS_ORIGINS (คั่นด้วย comma) ใน .env
# ต้องเพิ่ม origin ของ client-server ที่พัฒนาแยกอีกฝั่ง ไม่งั้น browser จะบล็อก CORS
_frontend_origin = os.getenv("FRONTEND_URL", "").strip().rstrip("/") or "http://localhost:5173"
_cors_origins = {
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    _frontend_origin,
}
for _origin in os.getenv("CORS_ORIGINS", "").split(","):
    _origin = _origin.strip().rstrip("/")
    if _origin:
        _cors_origins.add(_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(_cors_origins),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def migrate_reservation_booking():
    """เพิ่มคอลัมน์ note ให้ตารางที่มีอยู่ก่อน (create_all ไม่เพิ่มคอลัมน์ให้ตารางเก่า)"""
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE reservation_booking ADD COLUMN IF NOT EXISTS note TEXT"))


def migrate_user_points():
    """เพิ่มคอลัมน์ points ให้ accounts_unifieduser (ตาราง Django เดิมไม่มี)

    ระบบคะแนน/บทลงโทษของเอกพลใช้คอลัมน์นี้ — ทำแบบ idempotent เหมือน migrate อื่น
    """
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE accounts_unifieduser "
                "ADD COLUMN IF NOT EXISTS points INTEGER NOT NULL DEFAULT 12"
            )
        )


def migrate_review_rating():
    """เปลี่ยนคอลัมน์ reviews.rating จาก integer เป็น float (รองรับครึ่งดาว)

    create_all ไม่แก้ type คอลัมน์เก่า — ต้อง ALTER เองแบบ idempotent
    """
    with engine.begin() as connection:
        col_type = connection.execute(text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = 'reviews' AND column_name = 'rating'"
        )).scalar()
        if col_type is None:
            return  # ตารางยังไม่ถูกสร้าง (DB ใหม่) — create_all จะสร้างเป็น float ให้เอง
        if col_type in ("integer", "bigint", "smallint", "numeric"):
            connection.execute(text(
                "ALTER TABLE reviews ALTER COLUMN rating TYPE DOUBLE PRECISION "
                "USING rating::DOUBLE PRECISION"
            ))


def migrate_new_columns():
    """เพิ่มคอลัมน์ที่เพิ่มใหม่ให้ตารางเดิมแบบ idempotent (create_all ไม่เพิ่มคอลัมน์ให้ตารางเก่า)

    - bicycle: คอลัมน์จัดการจักรยาน M02 (แถว seed เดิมค่า NULL → GET fallback ไป BIKE_PRESENTATION)
    - maintenance_reports.images: รูปแนบตอนแจ้งซ่อม
    - reservation_booking: ธงแจ้งเตือนอัตโนมัติ (เตือน 15 นาทีก่อนรับรถ / เลยกำหนดคืน)
    """
    statements = (
        "ALTER TABLE bicycle ADD COLUMN IF NOT EXISTS code VARCHAR(20)",
        "ALTER TABLE bicycle ADD COLUMN IF NOT EXISTS type VARCHAR(50)",
        "ALTER TABLE bicycle ADD COLUMN IF NOT EXISTS model VARCHAR(100)",
        "ALTER TABLE bicycle ADD COLUMN IF NOT EXISTS station VARCHAR(100)",
        "ALTER TABLE bicycle ADD COLUMN IF NOT EXISTS distance VARCHAR(20)",
        "ALTER TABLE bicycle ADD COLUMN IF NOT EXISTS tint VARCHAR(20)",
        "ALTER TABLE bicycle ADD COLUMN IF NOT EXISTS battery INTEGER",
        "ALTER TABLE bicycle ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE maintenance_reports ADD COLUMN IF NOT EXISTS images JSONB",
        "ALTER TABLE reservation_booking ADD COLUMN IF NOT EXISTS pickup_reminded_at TIMESTAMPTZ",
        "ALTER TABLE reservation_booking ADD COLUMN IF NOT EXISTS overdue_notified_at TIMESTAMPTZ",
    )
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        # seed เดิม INSERT id ตรง ๆ ไม่ขยับ sequence → ทำให้ POST /bicycles ใหม่ชน duplicate key
        connection.execute(text(
            "SELECT setval(pg_get_serial_sequence('bicycle', 'id'), "
            "GREATEST(COALESCE((SELECT MAX(id) FROM bicycle), 1), 1))"
        ))

@app.on_event("startup")
def startup():
    # ต้องสร้างตารางก่อนเสมอ ไม่งั้น migrate_reservation_booking() จะ ALTER ตารางที่ยังไม่มี
    # (พังทันทีถ้าเป็น DB ใหม่ที่ยังไม่เคย seed)
    Base.metadata.create_all(bind=engine, tables=TABLES)
    migrate_reservation_booking()
    migrate_user_points()
    migrate_review_rating()
    migrate_new_columns()
    seed_bicycles()
    seed_main()


@app.on_event("startup")
async def start_reminder_task():
    """เปิด background task แจ้งเตือนอัตโนมัติ (เตือนก่อนรับรถ / เลยกำหนดคืน)"""
    await nathida_reminders.start_reminder_task()


@app.on_event("shutdown")
async def stop_reminder_task():
    await nathida_reminders.stop_reminder_task()

