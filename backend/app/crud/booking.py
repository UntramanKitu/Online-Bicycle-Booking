from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
from app.models.booking import ReservationBooking, UsageHistoryLog, SupportTicket
from app.schemas.booking import (
    ReservationBookingCreate, ReservationBookingUpdate,
    UsageHistoryLogCreate, UsageHistoryLogUpdate,
    SupportTicketCreate, SupportTicketUpdate
)


# สถานะที่ถือว่าจักรยานถูกใช้งาน/จองอยู่ (ยังไม่จบ)
ACTIVE_BOOKING_STATUSES = ("pending", "confirmed", "in_progress")


class BookingConflictError(Exception):
    """จักรยานไม่ว่างในช่วงเวลาที่ขอจอง (Availability) — เปลี่ยนเป็น HTTPException 409 ที่ router"""


class BookingStateError(Exception):
    """การเปลี่ยนสถานะ booking ไม่เป็นไปตาม lifecycle ที่กำหนด"""


# ==================== ReservationBooking CRUD ====================

def check_booking_availability(
    db: Session,
    bicycle_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[int] = None,
) -> bool:
    """ตรวจสอบความพร้อมใช้งาน (Availability) ของจักรยานในช่วงเวลาที่ระบุ
    คืนค่า True หากมี Booking ที่ยัง active (pending/confirmed/in_progress) ซ้อนทับเวลา"""
    query = db.query(ReservationBooking).filter(
        ReservationBooking.bicycle_id == bicycle_id,
        ReservationBooking.status.in_(ACTIVE_BOOKING_STATUSES),
        ReservationBooking.start_time < end_time,
        ReservationBooking.end_time > start_time,
    )
    if exclude_booking_id is not None:
        query = query.filter(ReservationBooking.id != exclude_booking_id)
    return query.first() is not None


def get_booking(db: Session, booking_id: int) -> Optional[ReservationBooking]:
    return db.query(ReservationBooking).filter(ReservationBooking.id == booking_id).first()


def get_bookings(db: Session, skip: int = 0, limit: int = 100) -> List[ReservationBooking]:
    return db.query(ReservationBooking).offset(skip).limit(limit).all()


def get_bookings_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[ReservationBooking]:
    return db.query(ReservationBooking).filter(ReservationBooking.user_id == user_id).offset(skip).limit(limit).all()


def get_bookings_by_bicycle(db: Session, bicycle_id: int, skip: int = 0, limit: int = 100) -> List[ReservationBooking]:
    return db.query(ReservationBooking).filter(ReservationBooking.bicycle_id == bicycle_id).offset(skip).limit(limit).all()


def get_bookings_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[ReservationBooking]:
    return db.query(ReservationBooking).filter(ReservationBooking.status == status).offset(skip).limit(limit).all()


def get_bookings_in_date_range(db: Session, start: datetime, end: datetime, skip: int = 0, limit: int = 100) -> List[ReservationBooking]:
    return db.query(ReservationBooking).filter(
        and_(ReservationBooking.start_time >= start, ReservationBooking.end_time <= end)
    ).offset(skip).limit(limit).all()


def create_booking(db: Session, booking: ReservationBookingCreate) -> ReservationBooking:
    """Create – เพิ่มการจองจักรยานล่วงหน้า
    พร้อมตรวจสอบ Availability ว่าจักรยานว่างในช่วงเวลานั้นหรือไม่"""
    if check_booking_availability(db, booking.bicycle_id, booking.start_time, booking.end_time):
        raise BookingConflictError(
            f"Bicycle {booking.bicycle_id} is not available from {booking.start_time} to {booking.end_time}"
        )

    db_booking = ReservationBooking(
        user_id=booking.user_id,
        bicycle_id=booking.bicycle_id,
        booking_type=booking.booking_type,
        start_time=booking.start_time,
        end_time=booking.end_time,
        pickup_location=booking.pickup_location,
        return_location=booking.return_location,
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def update_booking(db: Session, booking_id: int, booking: ReservationBookingUpdate) -> Optional[ReservationBooking]:
    """Update – แก้ไขการจอง เช่น เปลี่ยนเวลา/เริ่มยืม
    ถ้ามีการเปลี่ยนเวลา → ตรวจสอบ Availability ซ้ำ (ไม่นับ booking รายการนี้เอง)"""
    db_booking = get_booking(db, booking_id)
    if db_booking is None:
        return None
    update_data = booking.model_dump(exclude_unset=True)

    new_start = update_data.get("start_time", db_booking.start_time)
    new_end = update_data.get("end_time", db_booking.end_time)
    if "start_time" in update_data or "end_time" in update_data:
        if check_booking_availability(
            db, db_booking.bicycle_id, new_start, new_end, exclude_booking_id=booking_id
        ):
            raise BookingConflictError(
                f"Bicycle {db_booking.bicycle_id} is not available from {new_start} to {new_end}"
            )

    for key, value in update_data.items():
        setattr(db_booking, key, value)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def delete_booking(db: Session, booking_id: int) -> bool:
    db_booking = get_booking(db, booking_id)
    if db_booking is None:
        return False
    db.delete(db_booking)
    db.commit()
    return True


# ==================== UsageHistoryLog CRUD ====================

def get_usage_history(db: Session, history_id: int) -> Optional[UsageHistoryLog]:
    return db.query(UsageHistoryLog).filter(UsageHistoryLog.id == history_id).first()


def get_usage_histories(db: Session, skip: int = 0, limit: int = 100) -> List[UsageHistoryLog]:
    return db.query(UsageHistoryLog).offset(skip).limit(limit).all()


def get_usage_histories_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[UsageHistoryLog]:
    return db.query(UsageHistoryLog).filter(UsageHistoryLog.user_id == user_id).offset(skip).limit(limit).all()


def get_usage_histories_by_bicycle(db: Session, bicycle_id: int, skip: int = 0, limit: int = 100) -> List[UsageHistoryLog]:
    return db.query(UsageHistoryLog).filter(UsageHistoryLog.bicycle_id == bicycle_id).offset(skip).limit(limit).all()


def get_usage_histories_by_booking(db: Session, booking_id: int) -> Optional[UsageHistoryLog]:
    return db.query(UsageHistoryLog).filter(UsageHistoryLog.booking_id == booking_id).first()


def create_usage_history(db: Session, history: UsageHistoryLogCreate) -> UsageHistoryLog:
    db_history = UsageHistoryLog(
        user_id=history.user_id,
        bicycle_id=history.bicycle_id,
        booking_id=history.booking_id,
        start_time=history.start_time,
        end_time=history.end_time,
        duration_minutes=history.duration_minutes,
        distance_km=history.distance_km,
        starting_station=history.starting_station,
        ending_station=history.ending_station,
        status=history.status,
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history


def update_usage_history(db: Session, history_id: int, history: UsageHistoryLogUpdate) -> Optional[UsageHistoryLog]:
    db_history = get_usage_history(db, history_id)
    if db_history is None:
        return None
    update_data = history.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_history, key, value)
    db.commit()
    db.refresh(db_history)
    return db_history


def delete_usage_history(db: Session, history_id: int) -> bool:
    db_history = get_usage_history(db, history_id)
    if db_history is None:
        return False
    db.delete(db_history)
    db.commit()
    return True


# ==================== SupportTicket CRUD ====================

def get_ticket(db: Session, ticket_id: int) -> Optional[SupportTicket]:
    return db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()


def get_tickets(db: Session, skip: int = 0, limit: int = 100) -> List[SupportTicket]:
    return db.query(SupportTicket).offset(skip).limit(limit).all()


def get_tickets_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[SupportTicket]:
    return db.query(SupportTicket).filter(SupportTicket.user_id == user_id).offset(skip).limit(limit).all()


def get_tickets_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[SupportTicket]:
    return db.query(SupportTicket).filter(SupportTicket.status == status).offset(skip).limit(limit).all()


def get_tickets_by_category(db: Session, category: str, skip: int = 0, limit: int = 100) -> List[SupportTicket]:
    return db.query(SupportTicket).filter(SupportTicket.category == category).offset(skip).limit(limit).all()


def get_tickets_by_priority(db: Session, priority: str, skip: int = 0, limit: int = 100) -> List[SupportTicket]:
    return db.query(SupportTicket).filter(SupportTicket.priority == priority).offset(skip).limit(limit).all()


def get_tickets_assigned_to(db: Session, staff_id: int, skip: int = 0, limit: int = 100) -> List[SupportTicket]:
    return db.query(SupportTicket).filter(SupportTicket.assigned_to == staff_id).offset(skip).limit(limit).all()


def create_ticket(db: Session, ticket: SupportTicketCreate) -> SupportTicket:
    db_ticket = SupportTicket(
        user_id=ticket.user_id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket(db: Session, ticket_id: int, ticket: SupportTicketUpdate) -> Optional[SupportTicket]:
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket is None:
        return None
    update_data = ticket.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ticket, key, value)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: int, user_id: Optional[int] = None) -> bool:
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket is None:
        return False
    if user_id is not None and db_ticket.user_id != user_id:
        raise ValueError("คุณไม่มีสิทธิ์ลบคำร้องนี้")
    if db_ticket.status != "closed":
        raise ValueError("ลบได้เฉพาะคำร้องที่ปิดเคสแล้ว")
    db.delete(db_ticket)
    db.commit()
    return True


def change_booking_state(
    db: Session, booking_id: int, user_id: int, next_status: str
) -> Optional[ReservationBooking]:
    db_booking = get_booking(db, booking_id)
    if db_booking is None:
        return None
    if db_booking.user_id != user_id:
        raise BookingStateError("คุณไม่มีสิทธิ์จัดการ booking นี้")

    allowed = {
        "in_progress": {"pending", "confirmed"},
        "completed": {"in_progress"},
        "cancelled": {"pending", "confirmed"},
    }
    if db_booking.status not in allowed[next_status]:
        raise BookingStateError(
            f"ไม่สามารถเปลี่ยนสถานะจาก {db_booking.status} เป็น {next_status} ได้"
        )

    setattr(db_booking, "status", next_status)
    if next_status == "in_progress":
        db_booking.checked_out_at = datetime.utcnow()
    if next_status == "completed":
        db_booking.checked_in_at = datetime.utcnow()
    db.commit()
    db.refresh(db_booking)
    return db_booking