from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from database import Base


class ReturnStatus(str, enum.Enum):
    ON_TIME = "on_time"
    LATE = "late"
    DAMAGED = "damaged"


class PenaltyStatus(str, enum.Enum):
    ACTIVE = "active"
    APPEALED = "appealed"
    REMOVED = "removed"


class ReturnRecord(Base):
    __tablename__ = "return_records"

    id = Column(Integer, primary_key=True, index=True)
    bike_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    return_time = Column(DateTime, nullable=False)
    station = Column(String(100), nullable=False)
    status = Column(SAEnum(ReturnStatus), default=ReturnStatus.ON_TIME)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    damages = relationship("DamageEvidence", back_populates="return_record", cascade="all, delete-orphan")
    penalties = relationship("PenaltyStrike", back_populates="return_record", cascade="all, delete-orphan")


class DamageEvidence(Base):
    __tablename__ = "damage_evidence"

    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(Integer, ForeignKey("return_records.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    image_paths = Column(Text, nullable=True)
    severity = Column(String(20), default="minor")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    return_record = relationship("ReturnRecord", back_populates="damages")


class PenaltyStrike(Base):
    __tablename__ = "penalty_strikes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    return_id = Column(Integer, ForeignKey("return_records.id", ondelete="SET NULL"), nullable=True)
    points = Column(Integer, nullable=False, default=1)
    reason = Column(Text, nullable=False)
    status = Column(SAEnum(PenaltyStatus), default=PenaltyStatus.ACTIVE)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    return_record = relationship("ReturnRecord", back_populates="penalties")
