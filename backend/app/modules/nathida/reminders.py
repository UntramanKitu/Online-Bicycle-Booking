"""แจ้งเตือนอัตโนมัติฝั่งเซิร์ฟเวอร์ (FR3.6) — ของ Nathida

ทำงานเป็น background task ทุก 60 วินาที:
1. เตือนก่อนเวลารับรถ 15 นาที (pending/confirmed ที่ยังไม่เคยเตือน)
2. เตือนเมื่อเลยกำหนดคืนรถ (in_progress ที่ end_time ผ่านไปแล้ว)

ใช้คอลัมน์ pickup_reminded_at / overdue_notified_at เป็นธงกันส่งซ้ำ
(เพิ่มด้วย ALTER ... IF NOT EXISTS ที่ main.py)
"""

import asyncio
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models.booking import ReservationBooking
from app.models.nathida import Notification

REMIND_BEFORE = timedelta(minutes=15)
TICK_SECONDS = 60


def _notify(db, user_id: int, title: str, message: str) -> None:
    db.add(Notification(user_id=user_id, title=title, message=message))


def _tick() -> None:
    """รอบเดียวของการตรวจ — ทั้ง insert notification และตั้งธงกันซ้ำใน transaction เดียว"""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # 1) เตือนก่อนเวลารับรถ 15 นาที
        reminders = (
            db.query(ReservationBooking)
            .filter(
                ReservationBooking.status.in_(("pending", "confirmed")),
                ReservationBooking.pickup_reminded_at.is_(None),
                ReservationBooking.start_time <= now + REMIND_BEFORE,
                ReservationBooking.start_time > now,
            )
            .all()
        )
        for booking in reminders:
            _notify(
                db,
                booking.user_id,
                "ใกล้ถึงเวลาไปรับรถแล้ว",
                (
                    f"อีกไม่เกิน 15 นาที ถึงเวลารับจักรยาน #{booking.bicycle_id} "
                    f"เวลา {booking.start_time.astimezone():%d/%m/%Y %H:%M} "
                    f"ที่ {booking.pickup_location or 'จุดรับรถ'}"
                ),
            )
            booking.pickup_reminded_at = now

        # 2) เตือนเมื่อเลยกำหนดคืนรถ
        overdue = (
            db.query(ReservationBooking)
            .filter(
                ReservationBooking.status == "in_progress",
                ReservationBooking.overdue_notified_at.is_(None),
                ReservationBooking.end_time <= now,
            )
            .all()
        )
        for booking in overdue:
            _notify(
                db,
                booking.user_id,
                "เลยกำหนดคืนรถ",
                (
                    f"การยืมจักรยาน #{booking.bicycle_id} เลยกำหนดคืนแล้ว "
                    f"(กำหนดคืน {booking.end_time.astimezone():%d/%m/%Y %H:%M}) "
                    "กรุณานำรถมาคืนโดยเร็ว — หากคืนอาจถูกคิดค่าปรับ"
                ),
            )
            booking.overdue_notified_at = now

        if reminders or overdue:
            db.commit()
    except Exception as exc:  # ห้ามให้ task ตาย — log แล้วรอบหน้าลองใหม่
        db.rollback()
        print(f"[reminders] tick error: {exc}")
    finally:
        db.close()


async def reminder_loop():
    """วนตรวจทุก 60 วินาที — ทำงานแม้ไม่มีใครเปิดหน้าเว็บ (ต่างจากฝั่ง client เดิม)"""
    while True:
        _tick()
        await asyncio.sleep(TICK_SECONDS)


reminder_task: asyncio.Task | None = None


async def start_reminder_task() -> None:
    global reminder_task
    if reminder_task is None or reminder_task.done():
        reminder_task = asyncio.create_task(reminder_loop())


async def stop_reminder_task() -> None:
    global reminder_task
    if reminder_task is not None:
        reminder_task.cancel()
        reminder_task = None
