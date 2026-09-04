from sqlalchemy import Column, Integer
from app.database import Base

class UnifiedUser(Base):
    __tablename__ = "unified_user"
    id = Column(Integer, primary_key=True, index=True)