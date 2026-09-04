from sqlalchemy import Column, Integer
from app.database import Base

class StaffOfficer(Base):
    __tablename__ = "staff_officer"
    id = Column(Integer, primary_key=True, index=True)