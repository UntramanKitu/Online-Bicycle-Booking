"""ตาราง unified user ที่ตรงกับฝั่ง Django Monolith (branch TWO)

ฝั่ง Django ตั้ง AUTH_USER_MODEL = 'accounts.UnifiedUser' (สืบทอด AbstractUser)
และไม่ได้กำหนด Meta.db_table จึงได้ชื่อตาราง default = accounts_unifieduser

model นี้ mirror คอลัมน์ของ Django ทุกตัวเพื่อให้สองฝั่งใช้ตารางเดียวกันได้
หมายเหตุ: groups / user_permissions เป็นตาราง M2M ที่ Django สร้างเอง
ฝั่งนี้ไม่ declare เพราะไม่ได้ใช้งาน
"""

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String

from app.database import Base


class UnifiedUser(Base):
    __tablename__ = "accounts_unifieduser"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    password = Column(String(128), nullable=False, default="")
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    # username / first_name / last_name / email ใน AbstractUser เป็น blank=True
    # → Django สร้างเป็น NOT NULL ค่าเริ่มต้นคือ "" ไม่ใช่ NULL
    username = Column(String(150), nullable=False, unique=True, default="", index=True)
    first_name = Column(String(150), nullable=False, default="")
    last_name = Column(String(150), nullable=False, default="")
    email = Column(String(254), nullable=False, default="")
    is_staff = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    date_joined = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    points = Column(Integer, nullable=False, default=12)

    @property
    def full_name(self) -> str:
        """เทียบเท่า AbstractUser.get_full_name() — ไม่ใช่คอลัมน์"""
        combined = f"{self.first_name} {self.last_name}".strip()
        return combined or (self.username or "")