from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class GroupRide(Base):
    """ตารางกลุ่มปั่นร่วมกัน (Group Ride Bookings) — นายชัยอนันต์

    ระบบที่ให้นักศึกษาสามารถตั้งกลุ่มปั่นจักรยานไปยังจุดหมายต่างๆ
    ในมหาวิทยาลัยร่วมกัน เพื่อหาเพื่อนร่วมทางและเพิ่มความปลอดภัย
    ในการเดินทางเป็นกลุ่ม
    """

    __tablename__ = "group_ride"

    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, nullable=False)  # หัวหน้ากลุ่ม (user_id)
    name = Column(String(255), nullable=False)  # ชื่อกลุ่ม
    destination = Column(String(255), nullable=False)  # จุดหมายปลายทาง
    meetup_location = Column(String(255), nullable=True)  # สถานที่นัดพบ
    meetup_time = Column(DateTime(timezone=True), nullable=False)  # เวลานัดหมาย
    max_members = Column(Integer, nullable=False, default=4)  # จำนวนสมาชิกที่เปิดรับ
    current_members = Column(Integer, nullable=False, default=1)  # จำนวนสมาชิกปัจจุบัน (รวมหัวหน้า)
    status = Column(ENUM(
        "open", "full", "cancelled", "completed",
        name="group_ride_status", create_type=True
    ), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class GroupRideMember(Base):
    """ตารางสมาชิกกลุ่มปั่น — รองรับการเข้าร่วม/ออกจากกลุ่ม

    ใช้ติดตามว่าใครเข้าร่วมกลุ่มไหน (รวมหัวหน้ากลุ่ม) เพื่อรองรับ
    "เข้าร่วมกลุ่ม" และ "ออกจากกลุ่มเพื่อคืนโควตา" ตาม spec ของชัยอนันต์
    """

    __tablename__ = "group_ride_member"
    __table_args__ = (
        UniqueConstraint("group_ride_id", "user_id", name="uq_group_ride_member"),
    )

    id = Column(Integer, primary_key=True, index=True)
    group_ride_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(ENUM(
        "leader", "member",
        name="group_ride_member_role", create_type=True
    ), nullable=False, default="member")
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    left_at = Column(DateTime(timezone=True), nullable=True)  # เซ็ตเมื่อออกจากกลุ่ม (เก็บประวัติ)