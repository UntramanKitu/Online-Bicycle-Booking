from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.crud.booking import (
    BookingConflictError,
    BookingStateError,
    get_booking, get_bookings, get_bookings_by_user, get_bookings_by_bicycle,
    get_bookings_by_status, get_bookings_in_date_range,
    create_booking, update_booking, delete_booking, clear_booking_history,
    change_booking_state,
)
from app.schemas.booking import (
    ReservationBookingCreate, ReservationBookingUpdate, ReservationBookingResponse,
)
from app.models.nathida import Notification
from app.models.unified_user import UnifiedUser
from app.modules.auth.roles import resolve_role

router = APIRouter()

# งดยืมอัตโนมัติ (M12): แต้มต่ำกว่าเกณฑ์นี้ → จอง/ยืมจักรยานไม่ได้ (เกณฑ์เดียวกับหน้า "คะแนน & บทลงโทษ")
MIN_BORROW_POINTS = 6


def _check_borrow_allowed(db: Session, user_id: int) -> None:
    """ตรวจสิทธิ์การจอง/ยืมของผู้ใช้ — 403 ถ้าแต้มต่ำกว่าเกณฑ์หรือบัญชีถูกปิด"""
    user = db.get(UnifiedUser, user_id)
    if user is None:
        return  # ไม่พบผู้ใช้ → ปล่อยให้ endpoint อื่นจัดการ (เช่น 404)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="บัญชีของคุณถูกปิดใช้งาน ติดต่อแอดมิน")
    points = user.points if user.points is not None else 12
    if points < MIN_BORROW_POINTS:
        raise HTTPException(
            status_code=403,
            detail=(
                f"แต้มของคุณต่ำกว่า {MIN_BORROW_POINTS} คะแนน "
                "ระบบงดยืม/จองจักรยานชั่วคราว — ติดต่อแอดมินเพื่อขอคืนสิทธิ์"
            ),
        )


@router.get("/bookings", response_model=List[ReservationBookingResponse])
def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    bicycle_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    if user_id:
        return get_bookings_by_user(db, user_id, skip=skip, limit=limit)
    if bicycle_id:
        return get_bookings_by_bicycle(db, bicycle_id, skip=skip, limit=limit)
    if status:
        return get_bookings_by_status(db, status, skip=skip, limit=limit)
    if start_date and end_date:
        return get_bookings_in_date_range(db, start_date, end_date, skip=skip, limit=limit)
    return get_bookings(db, skip=skip, limit=limit)


@router.get("/bookings/{booking_id}", response_model=ReservationBookingResponse)
def read_booking(booking_id: int, db: Session = Depends(get_db)):
    db_booking = get_booking(db, booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return db_booking


@router.post("/bookings", response_model=ReservationBookingResponse, status_code=201)
def create_new_booking(booking: ReservationBookingCreate, db: Session = Depends(get_db)):
    """Create – เพิ่มการจองจักรยานล่วงหน้า (ตรวจสอบ Availability ของจักรยานด้วย)"""
    _check_borrow_allowed(db, booking.user_id)  # M12: งดยืมอัตโนมัติเมื่อแต้มต่ำ
    try:
        return create_booking(db, booking)
    except BookingConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/bookings/{booking_id}", response_model=ReservationBookingResponse)
def update_existing_booking(booking_id: int, booking: ReservationBookingUpdate, db: Session = Depends(get_db)):
    """Update – แก้ไขการจอง เช่น เปลี่ยนเวลา/เริ่มยืม (ตรวจสอบ availability หากเปลี่ยนเวลา)"""
    try:
        db_booking = update_booking(db, booking_id, booking)
    except BookingConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return db_booking


@router.delete("/bookings/history")
def clear_history(
    user_id: int = Query(..., description="ID ผู้ใช้เจ้าของประวัติ"),
    db: Session = Depends(get_db),
):
    """Delete (ล้างประวัติ) – ลบรายการจองที่จบไปแล้วของผู้ใช้คนนี้

    ลบเฉพาะ completed / cancelled / no_show
    รายการที่ยัง active อยู่จะไม่ถูกลบ
    """
    removed = clear_booking_history(db, user_id)
    return {"removed": removed}


# ประกาศหลัง /bookings/history เสมอ ไม่งั้น "history" จะถูก match ไปหา {booking_id} ก่อน
@router.delete("/bookings/{booking_id}", status_code=204)
def delete_existing_booking(booking_id: int, db: Session = Depends(get_db)):
    deleted = delete_booking(db, booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Booking not found")
    return None


@router.post("/bookings/{booking_id}/borrow", response_model=ReservationBookingResponse)
def borrow_booking(
    booking_id: int,
    user_id: int = Query(..., description="ID ผู้จอง"),
    db: Session = Depends(get_db),
):
    """รับจักรยานจริง: pending/confirmed -> in_progress"""
    _check_borrow_allowed(db, user_id)  # M12: งดยืมอัตโนมัติเมื่อแต้มต่ำ
    try:
        booking = change_booking_state(db, booking_id, user_id, "in_progress")
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/bookings/{booking_id}/return", response_model=ReservationBookingResponse)
def return_booking(
    booking_id: int,
    user_id: int = Query(..., description="ID ผู้จอง"),
    db: Session = Depends(get_db),
):
    """คืนจักรยาน: in_progress -> completed"""
    try:
        booking = change_booking_state(db, booking_id, user_id, "completed")
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/bookings/{booking_id}/cancel", response_model=ReservationBookingResponse)
def cancel_booking(
    booking_id: int,
    user_id: int = Query(..., description="ID ผู้จอง"),
    db: Session = Depends(get_db),
):
    """ยกเลิกการจองก่อนเริ่มยืม: pending/confirmed -> cancelled"""
    try:
        booking = change_booking_state(db, booking_id, user_id, "cancelled")
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/bookings/{booking_id}/confirm", response_model=ReservationBookingResponse)
def confirm_booking(
    booking_id: int,
    user_id: int = Query(..., description="ID ผู้กดยืนยัน (แอดมินหรือเจ้าของจอง)"),
    db: Session = Depends(get_db),
):
    """ยืนยันการจอง (Confirm): pending -> confirmed — เฉพาะแอดมินหรือเจ้าของจอง
    พร้อมสร้างแจ้งเตือนอัตโนมัติให้เจ้าของ"""
    db_booking = get_booking(db, booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    actor = db.get(UnifiedUser, user_id)
    if actor is None:
        raise HTTPException(status_code=404, detail="User not found")
    if actor.id != db_booking.user_id and resolve_role(actor) != "admin":
        raise HTTPException(status_code=403, detail="เฉพาะแอดมินหรือเจ้าของจองเท่านั้นที่ยืนยันได้")
    try:
        booking = change_booking_state(db, booking_id, db_booking.user_id, "confirmed")
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # แจ้งเตือนอัตโนมัติไปยังเจ้าของจองว่าได้รับการยืนยันแล้ว
    db.add(Notification(
        user_id=booking.user_id,
        title="การจองได้รับการยืนยัน",
        message=(
            f"การจองจักรยาน #{booking.bicycle_id} ของคุณได้รับการยืนยันแล้ว "
            f"เวลารับรถ {booking.start_time:%d/%m/%Y %H:%M} ที่ {booking.pickup_location or 'จุดรับรถ'}"
        ),
    ))
    db.commit()
    return booking