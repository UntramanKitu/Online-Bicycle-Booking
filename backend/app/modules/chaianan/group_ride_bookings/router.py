from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud.group_ride import (
    GroupRideError,
    cancel_group_ride,
    create_group_ride,
    get_group_members,
    get_group_ride,
    get_group_rides,
    get_group_rides_by_creator,
    get_group_rides_by_status,
    get_group_rides_by_user,
    join_group_ride,
    leave_group_ride,
    update_group_ride,
)
from app.database import get_db
from app.schemas.group_ride import (
    GroupRideCreate,
    GroupRideDetailResponse,
    GroupRideJoinRequest,
    GroupRideMemberResponse,
    GroupRideResponse,
    GroupRideUpdate,
)

router = APIRouter()


@router.get("/group-rides", response_model=List[GroupRideResponse])
def list_group_rides(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    created_by: Optional[int] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Read (ค้นหา/ดูกลุ่ม): ดูรายชื่อกลุ่มปั่นรอบตัว (filter ด้วย status=open เป็นหลัก)
    เพื่อดูรายละเอียดและตัดสินใจเข้าร่วม"""
    if status:
        return get_group_rides_by_status(db, status, skip=skip, limit=limit)
    if created_by:
        return get_group_rides_by_creator(db, created_by, skip=skip, limit=limit)
    if user_id:
        return get_group_rides_by_user(db, user_id, skip=skip, limit=limit)
    return get_group_rides(db, skip=skip, limit=limit)


@router.get("/group-rides/{group_ride_id}", response_model=GroupRideDetailResponse)
def read_group_ride(group_ride_id: int, db: Session = Depends(get_db)):
    """ดูรายละเอียดกลุ่มพร้อมรายชื่อสมาชิกปัจจุบัน"""
    db_group = get_group_ride(db, group_ride_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group ride not found")
    db_group.members = get_group_members(db, group_ride_id)
    return db_group


@router.get("/group-rides/{group_ride_id}/members", response_model=List[GroupRideMemberResponse])
def read_group_members(group_ride_id: int, db: Session = Depends(get_db)):
    """ดูรายชื่อสมาชิกที่ยังอยู่ในกลุ่ม"""
    if get_group_ride(db, group_ride_id) is None:
        raise HTTPException(status_code=404, detail="Group ride not found")
    return get_group_members(db, group_ride_id)


@router.post("/group-rides", response_model=GroupRideResponse, status_code=201)
def create_new_group_ride(group: GroupRideCreate, db: Session = Depends(get_db)):
    """Create (สร้างกลุ่ม): ผู้ใช้ตั้งกลุ่มปั่นใหม่ ระบุชื่อกลุ่ม จุดหมายปลายทาง
    เวลานัดหมาย และจำนวนสมาชิกที่ต้องการเปิดรับ — หัวหน้านับเป็นสมาชิกคนแรก"""
    try:
        return create_group_ride(db, group)
    except GroupRideError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/group-rides/{group_ride_id}", response_model=GroupRideResponse)
def update_existing_group_ride(
    group_ride_id: int,
    group: GroupRideUpdate,
    user_id: int = Query(..., description="ID ของผู้ใช้ที่เรียก (ต้องเป็นหัวหน้ากลุ่ม)"),
    db: Session = Depends(get_db),
):
    """Update (แก้ไขกลุ่ม): เฉพาะหัวหน้ากลุ่ม แก้ไขเวลานัดหมาย / จุดหมายปลายทาง / จำนวนสมาชิก"""
    try:
        return update_group_ride(db, group_ride_id, user_id, group)
    except GroupRideError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/group-rides/{group_ride_id}/join", response_model=GroupRideResponse)
def join_existing_group_ride(group_ride_id: int, body: GroupRideJoinRequest, db: Session = Depends(get_db)):
    """Update (เข้าร่วมกลุ่ม): ระบบบวกเพิ่มจำนวนสมาชิก และเปลี่ยนสถานะเป็น Full หากคนเต็ม"""
    try:
        return join_group_ride(db, group_ride_id, body.user_id)
    except GroupRideError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/group-rides/{group_ride_id}/leave", response_model=GroupRideResponse)
def leave_existing_group_ride(group_ride_id: int, body: GroupRideJoinRequest, db: Session = Depends(get_db)):
    """Delete (ออกจากกลุ่ม): สมาชิกออกจากกลุ่มเพื่อคืนโควตาให้คนอื่น — จำนวนสมาชิกลด กลับเป็น Open"""
    try:
        return leave_group_ride(db, group_ride_id, body.user_id)
    except GroupRideError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/group-rides/{group_ride_id}", response_model=GroupRideResponse)
def cancel_existing_group_ride(
    group_ride_id: int,
    user_id: int = Query(..., description="ID ของผู้ใช้ที่เรียก (ต้องเป็นหัวหน้ากลุ่ม)"),
    db: Session = Depends(get_db),
):
    """Delete (ยกเลิกกลุ่ม): หัวหน้ากลุ่มกดยกเลิกกลุ่ม → สถานะเปลี่ยนเป็น Cancelled"""
    try:
        return cancel_group_ride(db, group_ride_id, user_id)
    except GroupRideError as e:
        raise HTTPException(status_code=400, detail=str(e))