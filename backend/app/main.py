import sys

from fastapi import Depends, FastAPI

# กัน App crash ตอน print ภาษาไทย/emoji ใน console/pipe ที่ encoding ไม่ใช่ UTF-8 (เช่น Windows cp874)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import usage_history, bicycle
from app.modules.chaianan.reservation_booking import router as reservation_booking
from app.modules.chaianan.group_ride_bookings import router as group_ride
from app.modules.chaianan.support_tickets import router as support_ticket
from app.models.bicycle import Bicycle
from app.models.booking import ReservationBooking, UsageHistoryLog, SupportTicket
from app.models.group_ride import GroupRide, GroupRideMember
from app.seed.seed_bookings import main as seed_main
from app.seed.seed_bicycles import main as seed_bicycles

app = FastAPI()

# Include routers
app.include_router(reservation_booking.router, prefix="/api", tags=["reservation-booking"])
app.include_router(usage_history.router, prefix="/api", tags=["usage-history"])
app.include_router(support_ticket.router, prefix="/api", tags=["support-ticket"])
app.include_router(group_ride.router, prefix="/api", tags=["group-ride"])
app.include_router(bicycle.router, prefix="/api", tags=["bicycle"])

# สร้างตาราง
Base.metadata.create_all(
    bind=engine,
    tables=[
        ReservationBooking.__table__,
        UsageHistoryLog.__table__,
        SupportTicket.__table__,
        GroupRide.__table__,
        GroupRideMember.__table__,
        Bicycle.__table__,
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.on_event("startup")
def startup():
    seed_bicycles()
    Base.metadata.create_all(
        bind=engine,
        tables=[
            ReservationBooking.__table__,
            UsageHistoryLog.__table__,
            SupportTicket.__table__,
            GroupRide.__table__,
            GroupRideMember.__table__,
            Bicycle.__table__,
        ]
    )
    seed_main()

