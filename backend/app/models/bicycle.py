from sqlalchemy import Column, Integer
from app.database import Base

class Bicycle(Base):
    __tablename__ = "bicycle"
    id = Column(Integer, primary_key=True, index=True)