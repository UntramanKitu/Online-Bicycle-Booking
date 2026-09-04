from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== GroupRide ====================
class GroupRideCreate(BaseModel):
    created_by: int  # หัวหน้ากลุ่ม (user_id)
    name: str  # ชื่อกลุ่ม
    destination: str  # จุดหมายปลายทาง
    meetup_time: datetime  # เวลานัดหมาย
    meetup_location: Optional[str] = None  # สถานที่นัดพบ
    max_members: Optional[int] = Field(default=4, ge=2)  # เปิดรับสมาชิกอย่างน้อย 2 คน (รวมหัวหน้า)


class GroupRideUpdate(BaseModel):
    name: Optional[str] = None
    destination: Optional[str] = None
    meetup_time: Optional[datetime] = None
    meetup_location: Optional[str] = None
    max_members: Optional[int] = Field(default=None, ge=2)


class GroupRideResponse(BaseModel):
    id: int
    created_by: int
    name: str
    destination: str
    meetup_location: Optional[str] = None
    meetup_time: datetime
    max_members: int
    current_members: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GroupRideDetailResponse(GroupRideResponse):
    """Response ของกลุ่มเดียว — ครอบสมาชิกปัจจุบันของกลุ่มด้วย"""

    members: List["GroupRideMemberResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ==================== GroupRideMember ====================
class GroupRideJoinRequest(BaseModel):
    """body สำหรับเข้าร่วม/ออกจากกลุ่ม — ระบุผู้ใช้ที่กระทำ"""

    user_id: int


class GroupRideMemberResponse(BaseModel):
    id: int
    group_ride_id: int
    user_id: int
    role: str
    joined_at: datetime
    left_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


GroupRideDetailResponse.model_rebuild()