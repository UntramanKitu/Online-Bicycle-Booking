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
from app.models.nathida import Notification
from app.models.unified_user import UnifiedUser
from app.schemas.group_ride import GroupRideCreate, GroupRideUpdate


class GroupRideError(Exception):
    """Error ทางธุรกิจของกลุ่มปั่นร่วมกัน (เปลี่ยนเป็น HTTPException ที่ router)"""


# ==================== การแจ้งเตือนเหตุการณ์กลุ่มปั่น ====================

def _user_label(db: Session, user_id: int) -> str:
    """ชื่อแสดงของผู้ใช้สำหรับข้อความแจ้งเตือน — ถ้าไม่มี user จริงใช้เลขแทน"""
    user = db.get(UnifiedUser, user_id)
    if user is None:
        return f"ผู้ใช้ #{user_id}"
    name = f"{user.first_name} {user.last_name}".strip()
    return name or user.username or f"ผู้ใช้ #{user_id}"


def _notify(db: Session, user_id: Optional[int], title: str, message: str) -> None:
    """สร้าง notification ใน transaction เดียวกับ operation หลัก — เรียกก่อน db.commit()

    ข้ามเงียบถ้า user_id ไม่มีอยู่จริง (ตาราง notifications มี FK ชี้ accounts_unifieduser
    แต่ group_ride_member ไม่มี FK จึงอาจมี user_id ปลอมจากการทดสอบ)
    """
    if user_id is None:
        return
    if db.get(UnifiedUser, user_id) is None:
        return
    db.add(Notification(user_id=user_id, title=title, message=message, is_read=False))


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


def get_user_active_group(db: Session, user_id: int, exclude_group_id: Optional[int] = None) -> Optional[GroupRide]:
    """กลุ่มที่ผู้ใช้ยังเป็นสมาชิกอยู่และยังใช้งานได้ (open/full) — กติกา 1 คน / 1 กลุ่ม

    ใช้ทั้งตอนสร้างกลุ่มและตอนเข้าร่วมกลุ่ม เพื่อป้องกันคน ๆ เดียวอยู่ในหลายกลุ่มพร้อมกัน
    (กลุ่มที่ถูกยกเลิก/สิ้นสุดแล้วไม่นับ ส่วนสมาชิกที่ left ไปแล้วก็ไม่นับ)
    """
    query = (
        db.query(GroupRide)
        .join(GroupRideMember, GroupRideMember.group_ride_id == GroupRide.id)
        .filter(
            GroupRideMember.user_id == user_id,
            GroupRideMember.left_at.is_(None),
            GroupRide.status.in_(("open", "full")),
        )
        .order_by(GroupRide.id.asc())
    )
    if exclude_group_id is not None:
        query = query.filter(GroupRide.id != exclude_group_id)
    return query.first()


# ==================== Create ====================

def create_group_ride(db: Session, group: GroupRideCreate) -> GroupRide:
    """หัวหน้ากลุ่มสร้างกลุ่มปั่นใหม่ — หัวหน้าจะถูกเพิ่มเป็นสมาชิก (role=leader) อัตโนมัติ"""
    if group.max_members < 2:
        raise GroupRideError("ต้องเปิดรับสมาชิกอย่างน้อย 2 คน (รวมหัวหน้ากลุ่ม)")

    # กติกา 1 คน / 1 กลุ่ม — ยังเป็นสมาชิกกลุ่มอื่นอยู่ สร้างกลุ่มใหม่ไม่ได้
    other_group = get_user_active_group(db, group.created_by)
    if other_group is not None:
        raise GroupRideError(
            f'คุณอยู่ในกลุ่ม "{other_group.name}" อยู่แล้ว — 1 คนอยู่ได้เพียง 1 กลุ่ม '
            "(ออกจากกลุ่มเดิมหรือยกเลิกกลุ่มก่อนจึงจะสร้างกลุ่มใหม่ได้)"
        )

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

    # แจ้งสมาชิก (ยกเว้นหัวหน้ากลุ่มที่เป็นคนแก้) ว่ากลุ่มถูกแก้ไข — เวลา/จุดหมายอาจเปลี่ยน
    if update_data:
        for member in get_group_members(db, group_ride_id):
            if member.user_id == user_id:
                continue
            _notify(
                db,
                member.user_id,
                "กลุ่มปั่นถูกแก้ไข",
                f'หัวหน้ากลุ่ม "{db_group.name}" แก้ไขรายละเอียดกลุ่ม — '
                "กรุณาตรวจสอบเวลานัดหมาย/จุดหมายใหม่",
            )

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

    # กติกา 1 คน / 1 กลุ่ม — ห้ามเข้ากลุ่มใหม่ขณะที่ยังเป็นสมาชิกกลุ่มอื่นที่ยัง active อยู่
    other_group = get_user_active_group(db, user_id, exclude_group_id=group_ride_id)
    if other_group is not None:
        raise GroupRideError(
            f'คุณอยู่ในกลุ่ม "{other_group.name}" อยู่แล้ว — 1 คนเข้าร่วมได้เพียง 1 กลุ่ม '
            "(ออกจากกลุ่มเดิมก่อนจึงจะเข้าร่วมกลุ่มใหม่ได้)"
        )

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

    # แจ้งหัวหน้ากลุ่มว่ามีคนเข้าร่วม (+ บอกด้วยถ้ากลุ่มเต็มเพราะการเข้าร่วมนี้)
    if db_group.created_by != user_id:
        full_note = " — กลุ่มเต็มแล้ว" if db_group.status == "full" else ""
        _notify(
            db,
            db_group.created_by,
            "มีผู้เข้าร่วมกลุ่มปั่น",
            f'{_user_label(db, user_id)} เข้าร่วมกลุ่ม "{db_group.name}" แล้ว '
            f"(สมาชิก {db_group.current_members}/{db_group.max_members}){full_note}",
        )
    # กลุ่มเต็ม → แจ้งสมาชิกทุกคน (ยกเว้นหัวหน้าที่ได้รับแจ้งด้านบนแล้ว)
    if db_group.status == "full":
        for member in get_group_members(db, group_ride_id):
            if member.user_id == db_group.created_by:
                continue
            _notify(
                db,
                member.user_id,
                "กลุ่มปั่นเต็มแล้ว",
                f'กลุ่ม "{db_group.name}" มีสมาชิกครบ {db_group.max_members} คนแล้ว — เตรียมตัวออกเดินทางได้เลย',
            )

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

    # แจ้งหัวหน้ากลุ่มว่ามีสมาชิกออกจากกลุ่ม (คืนโควตาให้เปิดรับใหม่)
    if db_group.created_by != user_id:
        _notify(
            db,
            db_group.created_by,
            "สมาชิกออกจากกลุ่มปั่น",
            f'{_user_label(db, user_id)} ออกจากกลุ่ม "{db_group.name}" แล้ว '
            f"(เหลือสมาชิก {db_group.current_members} คน — กลุ่มกลับเปิดรับสมาชิก)",
        )

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

    # แจ้งสมาชิกทุกคน (ยกเว้นหัวหน้ากลุ่มที่เป็นคนยกเลิก) ว่ากลุ่มถูกยกเลิก
    for member in get_group_members(db, group_ride_id):
        if member.user_id == user_id:
            continue
        _notify(
            db,
            member.user_id,
            "กลุ่มปั่นถูกยกเลิก",
            f'หัวหน้ากลุ่มยกเลิกกลุ่ม "{db_group.name}" — นัดหมายปั่นรอบนี้เป็นอันยกเลิก',
        )

    db.commit()
    db.refresh(db_group)
    return db_group


def clear_cancelled_group_rides(db: Session) -> int:
    """ลบกลุ่มปั่นที่ถูกยกเลิกแล้วทั้งหมด (พร้อมรายการสมาชิกของกลุ่มนั้น)

    ลบเฉพาะสถานะ cancelled เท่านั้น กลุ่มที่ยังใช้งานอยู่ (open/full) ไม่ถูกแตะ
    """
    db_groups = db.query(GroupRide).filter(GroupRide.status == "cancelled").all()
    group_ids = [g.id for g in db_groups]
    if group_ids:
        # ลบสมาชิกก่อนเสมอ ไม่งั้นจะชน foreign key
        db.query(GroupRideMember).filter(GroupRideMember.group_ride_id.in_(group_ids)).delete(
            synchronize_session=False
        )
        db.query(GroupRide).filter(GroupRide.id.in_(group_ids)).delete(synchronize_session=False)
        db.commit()
    return len(group_ids)