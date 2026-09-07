import sys

from fastapi import Depends, FastAPI
from sqlalchemy import text

# กัน App crash ตอน print ภาษาไทย/emoji ใน console/pipe ที่ encoding ไม่ใช่ UTF-8 (เช่น Windows cp874)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import bicycle, user
from app.modules.auth import router as auth
from app.modules.chaianan.reservation_booking import router as reservation_booking
from app.modules.chaianan.group_ride_bookings import router as group_ride
from app.modules.chaianan.support_tickets import router as support_ticket
from app.models.bicycle import Bicycle
from app.models.unified_user import UnifiedUser
from app.models.booking import ReservationBooking, SupportTicket
from app.models.group_ride import GroupRide, GroupRideMember
from app.seed.seed_bookings import main as seed_main
from app.seed.seed_bicycles import main as seed_bicycles

app = FastAPI()

# Include routers
app.include_router(reservation_booking.router, prefix="/api", tags=["reservation-booking"])
app.include_router(support_ticket.router, prefix="/api", tags=["support-ticket"])
app.include_router(group_ride.router, prefix="/api", tags=["group-ride"])
app.include_router(bicycle.router, prefix="/api", tags=["bicycle"])
app.include_router(user.router, prefix="/api", tags=["users"])
app.include_router(auth.router, prefix="/api")

# สร้างตาราง
Base.metadata.create_all(
    bind=engine,
    tables=[
        ReservationBooking.__table__,
        SupportTicket.__table__,
        GroupRide.__table__,
        GroupRideMember.__table__,
        Bicycle.__table__,
        UnifiedUser.__table__,
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def migrate_unified_user():
    with engine.begin() as connection:
        for column in ("google_sub", "email", "display_name", "avatar_url"):
            connection.execute(text(f"ALTER TABLE unified_user ADD COLUMN IF NOT EXISTS {column} VARCHAR(500)"))

@app.on_event("startup")
def startup():
    migrate_unified_user()
    seed_bicycles()
    Base.metadata.create_all(
        bind=engine,
        tables=[
            ReservationBooking.__table__,
            SupportTicket.__table__,
            GroupRide.__table__,
            GroupRideMember.__table__,
            Bicycle.__table__,
            UnifiedUser.__table__,
        ]
    )
    seed_main()

