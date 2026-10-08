from pydantic import BaseModel, Field


class BicycleResponse(BaseModel):
    id: int
    code: str
    type: str
    model: str
    station: str
    distance: str
    tint: str
    battery: int | None = None
    available: bool
    is_active: bool = True


class BicycleCreate(BaseModel):
    """เพิ่มจักรยานใหม่ (แอดมิน) — code ระบบสร้างให้ตามประเภท ไม่ต้องส่งมา"""

    type: str = Field("ธรรมดา", max_length=50)
    model: str = Field("จักรยาน", max_length=100)
    station: str = Field("สถานีหลัก", max_length=100)
    distance: str = Field("-", max_length=20)
    tint: str = Field("#e7f2ea", max_length=20)
    battery: int | None = Field(None, ge=0, le=100)


class BicycleUpdate(BaseModel):
    """แก้ไขข้อมูลจักรยาน (แอดมิน) — ส่งเฉพาะช่องที่อยากแก้"""

    code: str | None = Field(None, max_length=20)
    type: str | None = Field(None, max_length=50)
    model: str | None = Field(None, max_length=100)
    station: str | None = Field(None, max_length=100)
    distance: str | None = Field(None, max_length=20)
    tint: str | None = Field(None, max_length=20)
    battery: int | None = Field(None, ge=0, le=100)


class BicycleStatusUpdate(BaseModel):
    """เปิด/ปิดใช้จักรยาน"""

    is_active: bool
