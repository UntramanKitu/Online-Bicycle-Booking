from sqlalchemy import Column, Integer, String
from app.database import Base

class UnifiedUser(Base):
    __tablename__ = "unified_user"
    id = Column(Integer, primary_key=True, index=True)
    google_sub = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)