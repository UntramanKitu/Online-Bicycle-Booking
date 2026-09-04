from app.modules.chaiyanan.group_ride_bookings.crud import *
"""CRUD สำหรับ Group Ride Bookings (ตารางกลุ่มปั่นร่วมกัน) — นายชัยอนันต์

ครอบคลุม spec CRUD ในเอกสาร:
- Create (สร้างกลุ่ม)   : หัวหน้ากลุ่มตั้งกลุ่มปั่นใหม่ → หัวหน้านับเป็นสมาชิกคนแรก
- Read  (ค้นหา/ดูกลุ่ม) : ดูรายชื่อกลุ่มปั่น (โดยเฉพาะกลุ่มที่สถานะ Open)
- Update (เข้าร่วม/แก้ไข) :
    * ผู้ใช้ทั่วไปกด "เข้าร่วมกลุ่ม" → ระบบบวกจำนวนสมาชิก และเปลี่ยนเป็น Full เมื่อเต็ม
    * หัวหน้ากลุ่มแก้ไขเวลานัดหมาย / จุดหมายปลายทาง
- Delete (ยกเลิก/ออก):
    * หัวหน้ากลุ่มกดยกเลิกกลุ่ม → สถานะเปลี่ยนเป็น Cancelled
    * สมาชิกกดออกจากกลุ่ม → คืนโควตาให้คนอื่น (ลดจำนวนสมาชิก แล้วกลับเป็น Open)
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.group_ride import GroupRide, GroupRideMember
from app.schemas.group_ride import GroupRideCreate, GroupRideUpdate


class GroupRideError(Exception):
    """Error ทางธุรกิจของกลุ่มปั่นร่วมกัน (เปลี่ยนเป็น HTTPException ที่ router)"""


# ==================== Read ====================

def get_group_ride(db: Session, group_ride_id: int) -> Optional[GroupRide]:
    return db.query(GroupRide).filter(GroupRide.id == group_ride_id).first()


def get_group_rides(db: Session, skip: int = 0, limit: int = 100) -> List[GroupRide]:
    return (
        db.query(GroupRide)
        .order_by(GroupRide.meetup_time.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_group_rides_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[GroupRide]:
    return (
        db.query(GroupRide)
        .filter(GroupRide.status == status)
        .order_by(GroupRide.meetup_time.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_group_rides_by_creator(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[GroupRide]:
    return (
        db.query(GroupRide)
        .filter(GroupRide.created_by == user_id)
        .order_by(GroupRide.meetup_time.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_group_rides_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[GroupRide]:
    """กลุ่มทั้งหมดที่ผู้ใช้เข้าร่วมอยู่ (membership ที่ยังไม่ left)"""
    joined_ids = (
        db.query(GroupRideMember.group_ride_id)
        .filter(GroupRideMember.user_id == user_id, GroupRideMember.left_at.is_(None))
        .subquery()
    )
    return (
        db.query(GroupRide)
        .join(joined_ids, GroupRide.id == joined_ids.c.group_ride_id)
        .order_by(GroupRide.meetup_time.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_group_members(db: Session, group_ride_id: int) -> List[GroupRideMember]:
    """สมาชิกที่ยังอยู่ในกลุ่ม (ไม่รวมที่ออกไปแล้ว)"""
    return (
        db.query(GroupRideMember)
        .filter(GroupRideMember.group_ride_id == group_ride_id, GroupRideMember.left_at.is_(None))
        .order_by(GroupRideMember.joined_at.asc())
        .all()
    )


# ==================== Create ====================

def create_group_ride(db: Session, group: GroupRideCreate) -> GroupRide:
    """หัวหน้ากลุ่มสร้างกลุ่มปั่นใหม่ — หัวหน้าจะถูกเพิ่มเป็นสมาชิก (role=leader) อัตโนมัติ"""
    if group.max_members < 2:
        raise GroupRideError("ต้องเปิดรับสมาชิกอย่างน้อย 2 คน (รวมหัวหน้ากลุ่ม)")

    db_group = GroupRide(
        created_by=group.created_by,
        name=group.name,
        destination=group.destination,
        meetup_location=group.meetup_location,
        meetup_time=group.meetup_time,
        max_members=group.max_members,
        current_members=1,
        status="open",
    )
    db.add(db_group)
    db.flush()  # เพื่อให้ได้ id ของ group ก่อนสร้าง membership

    db.add(GroupRideMember(group_ride_id=db_group.id, user_id=group.created_by, role="leader"))

    db.commit()
    db.refresh(db_group)
    return db_group


# ==================== Update ====================

def update_group_ride(db: Session, group_ride_id: int, user_id: int, group: GroupRideUpdate) -> Optional[GroupRide]:
    """เฉพาะหัวหน้ากลุ่ม: แก้ไขชื่อกลุ่ม/จุดหมาย/เวลา/จำนวนสมาชิกที่เปิดรับ"""
    db_group = get_group_ride(db, group_ride_id)
    if db_group is None:
        raise GroupRideError("ไม่พบกลุ่มปั่นดังกล่าว")
    if db_group.created_by != user_id:
        raise GroupRideError("เฉพาะหัวหน้ากลุ่มเท่านั้นที่แก้ไขกลุ่มได้")
    if db_group.status in ("cancelled", "completed"):
        raise GroupRideError("กลุ่มถูกยกเลิก/สิ้นสุดแล้ว ไม่สามารถแก้ไขได้")

    update_data = group.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_group, key, value)

    # ตาม spec: "ระบบจะบวกเพิ่มจำนวนในฟิลด์ และเปลี่ยนสถานะเป็น Full หากคนเต็ม"
    if db_group.max_members is not None and db_group.current_members >= db_group.max_members:
        db_group.status = "full"
    else:
        db_group.status = "open"

    db.commit()
    db.refresh(db_group)
    return db_group


def join_group_ride(db: Session, group_ride_id: int, user_id: int) -> Optional[GroupRide]:
    """เข้าร่วมกลุ่ม — บวกจำนวนสมาชิก และเปลี่ยนสถานะเป็น Full เมื่อคนเต็ม"""
    db_group = get_group_ride(db, group_ride_id)
    if db_group is None:
        raise GroupRideError("ไม่พบกลุ่มปั่นดังกล่าว")
    if db_group.status == "cancelled":
        raise GroupRideError("กลุ่มนี้ถูกยกเลิกแล้ว ไม่สามารถเข้าร่วมได้")
    if db_group.status == "completed":
        raise GroupRideError("กลุ่มนี้สิ้นสุดแล้ว ไม่สามารถเข้าร่วมได้")

    existing = (
        db.query(GroupRideMember)
        .filter(
            GroupRideMember.group_ride_id == group_ride_id,
            GroupRideMember.user_id == user_id,
            GroupRideMember.left_at.is_(None),
        )
        .first()
    )
    if existing is not None:
        raise GroupRideError("คุณเข้าร่วมกลุ่มนี้อยู่แล้ว")

    if db_group.current_members >= db_group.max_members:
        raise GroupRideError("กลุ่มเต็มแล้ว ไม่สามารถเข้าร่วมได้")

    db_group.current_members += 1
    if db_group.current_members >= db_group.max_members:
        db_group.status = "full"

    # หากเคยออกจากกลุ่มมาก่อน → เข้าใหม่โดยใช้ record เดิม (หลีกเลี่ยง UNIQUE constraint ซ้ำ)
    previous = (
        db.query(GroupRideMember)
        .filter(
            GroupRideMember.group_ride_id == group_ride_id,
            GroupRideMember.user_id == user_id,
        )
        .first()
    )
    if previous is not None:
        previous.left_at = None
        previous.joined_at = datetime.now(timezone.utc)
    else:
        db.add(GroupRideMember(group_ride_id=group_ride_id, user_id=user_id, role="member"))

    db.commit()
    db.refresh(db_group)
    return db_group


def leave_group_ride(db: Session, group_ride_id: int, user_id: int) -> Optional[GroupRide]:
    """ออกจากกลุ่ม (ยกเว้นหัวหน้ากลุ่ม) — ลดจำนวนสมาชิก กลับเป็น Open เพื่อคืนโควตา"""
    db_group = get_group_ride(db, group_ride_id)
    if db_group is None:
        raise GroupRideError("ไม่พบกลุ่มปั่นดังกล่าว")

    membership = (
        db.query(GroupRideMember)
        .filter(
            GroupRideMember.group_ride_id == group_ride_id,
            GroupRideMember.user_id == user_id,
            GroupRideMember.left_at.is_(None),
        )
        .first()
    )
    if membership is None:
        raise GroupRideError("คุณไม่ได้เป็นสมาชิกของกลุ่มนี้")
    if membership.role == "leader":
        raise GroupRideError("หัวหน้ากลุ่มไม่สามารถออกจากกลุ่มได้ ให้ยกเลิกกลุ่มแทน")

    if db_group.status in ("cancelled", "completed"):
        raise GroupRideError("กลุ่มนี้ถูกยกเลิก/สิ้นสุดแล้ว ไม่ต้องออกจากกลุ่ม")

    membership.left_at = datetime.now(timezone.utc)
    db_group.current_members = max(1, db_group.current_members - 1)
    if db_group.current_members < db_group.max_members:
        db_group.status = "open"

    db.commit()
    db.refresh(db_group)
    return db_group


# ==================== Delete / Cancel ====================

def cancel_group_ride(db: Session, group_ride_id: int, user_id: int) -> Optional[GroupRide]:
    """ยกเลิกกลุ่ม (เฉพาะหัวหน้ากลุ่ม) — สถานะเปลี่ยนเป็น Cancelled ตาม spec"""
    db_group = get_group_ride(db, group_ride_id)
    if db_group is None:
        raise GroupRideError("ไม่พบกลุ่มปั่นดังกล่าว")
    if db_group.created_by != user_id:
        raise GroupRideError("เฉพาะหัวหน้ากลุ่มเท่านั้นที่ยกเลิกกลุ่มได้")
    if db_group.status == "cancelled":
        raise GroupRideError("กลุ่มนี้ถูกยกเลิกไปแล้ว")

    db_group.status = "cancelled"
    db.commit()
    db.refresh(db_group)
    return db_group