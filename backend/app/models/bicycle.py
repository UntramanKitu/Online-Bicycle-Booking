from sqlalchemy import Boolean, Column, Integer, String
from app.database import Base

class Bicycle(Base):
    __tablename__ = "bicycle"
    id = Column(Integer, primary_key=True, index=True)
    # คอลัมน์จัดการจักรยาน (M02) — เพิ่มทีหลังด้วย ALTER ... IF NOT EXISTS (create_all ไม่เพิ่มคอลัมน์ให้ตารางเก่า)
    # แถวเดิม (id 1-8 ที่ seed) ค่าจะเป็น NULL → ฝั่ง GET /bicycles จะ fallback ไป BIKE_PRESENTATION เหมือนเดิม
    code = Column(String(20), nullable=True)
    type = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    station = Column(String(100), nullable=True)
    distance = Column(String(20), nullable=True)
    tint = Column(String(20), nullable=True)
    battery = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)