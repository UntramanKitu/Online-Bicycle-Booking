from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.booking import ACTIVE_BOOKING_STATUSES
from app.database import get_db
from app.models.bicycle import Bicycle
from app.models.booking import ReservationBooking
from app.modules.auth.deps import require_admin
from app.schemas.bicycle import (
    BicycleCreate, BicycleResponse, BicycleStatusUpdate, BicycleUpdate,
)

router = APIRouter()

BIKE_TYPE_PREFIX = {
    'ไฟฟ้า': 'E',
    'ธรรมดา': 'N',
    'พับได้': 'P',
    'เสือภูเขา': 'T',
}


def _next_code_for_type(db: Session, bike_type: str) -> str:
    """รหัสออโต้ตามประเภท: E-BIKE-001 (ไฟฟ้า) / N-BIKE-001 (ธรรมดา) / P-BIKE-001 (พับได้) / T-BIKE-001 (เสือภูเขา)"""
    prefix = BIKE_TYPE_PREFIX.get((bike_type or '').strip(), 'N')
    like = f'{prefix}-BIKE-%'
    max_num = 0
    for (code,) in db.query(Bicycle.code).filter(Bicycle.code.like(like)).all():
        try:
            num = int(str(code).rsplit('-', 1)[-1])
        except (ValueError, IndexError):
            continue
        max_num = max(max_num, num)
    return f'{prefix}-BIKE-{max_num + 1:03d}'

BIKE_PRESENTATION = {
    1: ('ธรรมดา', 'เสือหมอบ', 'สถานีคณะวิศวะ', '80 ม.', '#e7f2ea', None),
    2: ('ไฟฟ้า', 'ไฟฟ้า E-Bike', 'สถานีหอสมุด', '150 ม.', '#e2f0e9', 82),
    3: ('ธรรมดา', 'ธรรมดา', 'สถานีโรงอาหารกลาง', '40 ม.', '#eef1ef', None),
    4: ('พับได้', 'พับได้', 'สถานีหอพัก 2', '300 ม.', '#e7f2ea', None),
    5: ('ไฟฟ้า', 'ไฟฟ้า E-Bike', 'สถานีคณะวิทยาศาสตร์', '210 ม.', '#e2f0e9', 45),
    6: ('เสือภูเขา', 'เสือภูเขา', 'สถานีสนามกีฬา', '95 ม.', '#e7f2ea', None),
    7: ('ธรรมดา', 'ธรรมดา', 'สถานีประตู 1', '60 ม.', '#eef1ef', None),
    8: ('ไฟฟ้า', 'ไฟฟ้า E-Bike', 'สถานีคณะบริหารธุรกิจ', '175 ม.', '#e2f0e9', 12),
}
PRESENTATION_FALLBACK = ('ธรรมดา', 'จักรยาน', 'สถานีหลัก', '-', '#e7f2ea', None)


def _active_booking_ids(db: Session) -> set[int]:
    """จักรยานที่มีคนใช้งานอยู่จริง ณ ตอนนี้ (จองซ้อนเวลาปัจจุบัน)"""
    now = datetime.now(timezone.utc)
    return {
        booking.bicycle_id
        for booking in db.query(ReservationBooking).filter(
            ReservationBooking.status.in_(ACTIVE_BOOKING_STATUSES),
            ReservationBooking.start_time <= now,
            ReservationBooking.end_time > now,
        ).all()
    }


def _to_response(db: Session, bicycle: Bicycle, active_ids: set[int]) -> BicycleResponse:
    """คอลัมน์ใหม่ค่า NULL (แถวเดิมที่ seed) → fallback ไป BIKE_PRESENTATION เหมือนเดิม"""
    legacy = BIKE_PRESENTATION.get(bicycle.id, PRESENTATION_FALLBACK)

    def pick(stored, idx):
        return stored if stored not in (None, "") else legacy[idx]

    return BicycleResponse(
        id=bicycle.id,
        code=bicycle.code or f'BIKE-{bicycle.id:03d}',
        type=pick(bicycle.type, 0),
        model=pick(bicycle.model, 1),
        station=pick(bicycle.station, 2),
        distance=pick(bicycle.distance, 3),
        tint=pick(bicycle.tint, 4),
        battery=bicycle.battery if bicycle.battery is not None else legacy[5],
        available=bicycle.is_active and bicycle.id not in active_ids,
        is_active=bicycle.is_active,
    )


def _check_code_unique(db: Session, code: str | None, exclude_id: int | None = None) -> None:
    if not code:
        return
    query = db.query(Bicycle).filter(Bicycle.code == code)
    if exclude_id is not None:
        query = query.filter(Bicycle.id != exclude_id)
    if query.first() is not None:
        raise HTTPException(status_code=409, detail=f'รหัสจักรยาน "{code}" มีอยู่ในระบบแล้ว')


@router.get('/bicycles', response_model=list[BicycleResponse])
def list_bicycles(db: Session = Depends(get_db)):
    active_ids = _active_booking_ids(db)
    return [
        _to_response(db, bicycle, active_ids)
        for bicycle in db.query(Bicycle).order_by(Bicycle.id).all()
    ]


@router.get('/bicycles/{bicycle_id}', response_model=BicycleResponse)
def read_bicycle(bicycle_id: int, db: Session = Depends(get_db)):
    bicycle = db.get(Bicycle, bicycle_id)
    if bicycle is None:
        raise HTTPException(status_code=404, detail='Bicycle not found')
    return _to_response(db, bicycle, _active_booking_ids(db))


# ==================== จัดการจักรยาน (M02 — แอดมิน) ====================
@router.post('/bicycles', response_model=BicycleResponse, status_code=201)
def create_bicycle(
    payload: BicycleCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """เพิ่มจักรยานใหม่ — ไม่รับ code จาก client แล้ว ระบบสร้างให้ตามประเภท (E/N/P/T-BIKE-xxx)"""
    bicycle = Bicycle(
        code=None,  # สร้างหลัง flush ตามประเภท
        type=payload.type,
        model=payload.model,
        station=payload.station,
        distance=payload.distance,
        tint=payload.tint,
        # แบตมีเฉพาะไฟฟ้า — ประเภทอื่นบังคับ null กันข้อมูลขยะ
        battery=payload.battery if payload.type == 'ไฟฟ้า' else None,
        is_active=True,
    )
    db.add(bicycle)
    db.flush()  # ได้ id ก่อน (เผื่อ fallback ตอนชน)
    bicycle.code = _next_code_for_type(db, payload.type)
    # กันชนกรณีแข่งกันสร้างพร้อมกัน — ถ้าชนให้เลื่อนเลขไปเรื่อย ๆ
    for _ in range(10):
        try:
            db.flush()
            break
        except IntegrityError:
            db.rollback()
            db.add(bicycle)
            num = int(bicycle.code.rsplit('-', 1)[-1]) + 1
            bicycle.code = f"{bicycle.code.rsplit('-', 1)[0]}-{num:03d}"
    db.commit()
    db.refresh(bicycle)
    return _to_response(db, bicycle, set())


@router.put('/bicycles/{bicycle_id}', response_model=BicycleResponse)
def update_bicycle(
    bicycle_id: int,
    payload: BicycleUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """แก้ไขข้อมูลจักรยาน (ส่งเฉพาะช่องที่เปลี่ยน)"""
    bicycle = db.get(Bicycle, bicycle_id)
    if bicycle is None:
        raise HTTPException(status_code=404, detail='Bicycle not found')
    data = payload.model_dump(exclude_unset=True)
    if 'code' in data:
        _check_code_unique(db, data['code'], exclude_id=bicycle_id)
    for key, value in data.items():
        setattr(bicycle, key, value)
    db.commit()
    db.refresh(bicycle)
    return _to_response(db, bicycle, _active_booking_ids(db))


@router.patch('/bicycles/{bicycle_id}/status', response_model=BicycleResponse)
def toggle_bicycle_status(
    bicycle_id: int,
    payload: BicycleStatusUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """เปิด/ปิดใช้จักรยาน — ปิดใช้แล้วจะจองไม่ได้ (available = false)"""
    bicycle = db.get(Bicycle, bicycle_id)
    if bicycle is None:
        raise HTTPException(status_code=404, detail='Bicycle not found')
    bicycle.is_active = payload.is_active
    db.commit()
    db.refresh(bicycle)
    return _to_response(db, bicycle, _active_booking_ids(db))


@router.delete('/bicycles/{bicycle_id}')
def delete_bicycle(
    bicycle_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """ลบจักรยาน — ถ้ามีคนใช้งานอยู่ตอนนี้หรือมีข้อมูลอ้างอิง (การจอง/รีวิว/แจ้งซ่อม) จะลบไม่ได้ ให้ใช้ปิดใช้แทน"""
    bicycle = db.get(Bicycle, bicycle_id)
    if bicycle is None:
        raise HTTPException(status_code=404, detail='Bicycle not found')
    if bicycle_id in _active_booking_ids(db):
        raise HTTPException(status_code=409, detail='จักรยานคันนี้กำลังถูกใช้งาน/จองอยู่ ไม่สามารถลบได้')
    try:
        db.delete(bicycle)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail='มีข้อมูลอ้างอิงจักรยานคันนี้ (การจอง/รีวิว/แจ้งซ่อม) — ใช้ "ปิดใช้" แทนการลบ',
        )
    return {'deleted': 1}

