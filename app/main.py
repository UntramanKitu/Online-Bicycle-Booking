"""จุดเริ่มต้นของ backend: สร้างแอป FastAPI แล้วรวม API ทั้ง 3 โมดูล"""

import logging
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import maintenance, notification, review
from app.database import Base, engine, get_db, settings
from app.models import Notification

logger = logging.getLogger(__name__)

app = FastAPI(title="Bicycle Booking System API (M13-M15)")

# อนุญาตให้ frontend (คนละพอร์ต) เรียก API ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notification.router)
app.include_router(maintenance.router)
app.include_router(review.router)


# สร้างตารางที่ยังไม่มีตอนเปิด backend
@app.on_event("startup")
def create_tables() -> None:
    try:
        Base.metadata.create_all(engine)
    except SQLAlchemyError as exc:
        logger.warning("Cannot connect to the database: %s", exc.__class__.__name__)


# error จากฐานข้อมูลทุกจุด -> ตอบ 503 โดยไม่เปิดเผยรายละเอียดการเชื่อมต่อ
@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.warning("Database error on %s %s: %s", request.method, request.url.path, exc.__class__.__name__)
    return JSONResponse(status_code=503, content={"detail": "Database connection failed. Check backend/.env."})


# ตรวจว่า backend และฐานข้อมูลทำงานอยู่ (หน้าแอดมินของ frontend เรียกใช้)
@app.get("/api/system/status", tags=["System"])
def system_status(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "backend": "connected",
        "database": "connected",
        "database_name": engine.url.database or "unknown",
        "notification_api": "connected",
        "notification_count": db.scalar(func.count(Notification.id)),
        "time": datetime.now(UTC),
        "version": "1.0",
    }
