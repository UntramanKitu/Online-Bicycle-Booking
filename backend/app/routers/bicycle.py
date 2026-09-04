from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.booking import ACTIVE_BOOKING_STATUSES
from app.database import get_db
from app.models.bicycle import Bicycle
from app.models.booking import ReservationBooking
from app.schemas.bicycle import BicycleResponse

router = APIRouter()

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


@router.get('/bicycles', response_model=list[BicycleResponse])
def list_bicycles(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    active_ids = {
        booking.bicycle_id
        for booking in db.query(ReservationBooking).filter(
            ReservationBooking.status.in_(ACTIVE_BOOKING_STATUSES),
            ReservationBooking.start_time <= now,
            ReservationBooking.end_time > now,
        ).all()
    }
    result = []
    for bicycle in db.query(Bicycle).order_by(Bicycle.id).all():
        bike_type, model, station, distance, tint, battery = BIKE_PRESENTATION.get(
            bicycle.id, ('ธรรมดา', 'จักรยาน', 'สถานีหลัก', '-', '#e7f2ea', None)
        )
        result.append(BicycleResponse(
            id=bicycle.id,
            code=f'BIKE-{bicycle.id:03d}',
            type=bike_type,
            model=model,
            station=station,
            distance=distance,
            tint=tint,
            battery=battery,
            available=bicycle.id not in active_ids,
        ))
    return result
