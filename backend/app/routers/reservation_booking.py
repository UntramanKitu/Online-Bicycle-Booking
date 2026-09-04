from app.modules.chaianan.reservation_booking.router import *
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.crud.booking import (
    BookingConflictError,
    get_booking, get_bookings, get_bookings_by_user, get_bookings_by_bicycle,
    get_bookings_by_status, get_bookings_in_date_range,
    create_booking, update_booking, delete_booking,
)
from app.schemas.booking import (
    ReservationBookingCreate, ReservationBookingUpdate, ReservationBookingResponse,
)

router = APIRouter()


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


@router.delete("/bookings/{booking_id}", status_code=204)
def delete_existing_booking(booking_id: int, db: Session = Depends(get_db)):
    deleted = delete_booking(db, booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Booking not found")
    return None