from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class FavoriteTargetType(str, enum.Enum):
    BICYCLE = "bicycle"
    STATION = "station"


class PenaltyReason(str, enum.Enum):
    LATE_RETURN = "late_return"
    DAMAGED = "damaged"
    LOST = "lost"
    OTHER = "other"
    GOOD_BEHAVIOR = "good_behavior"
    NO_VIOLATION_WEEK = "no_violation_week"


class Favorite(Base):
    __tablename__ = "favorite"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_unifieduser.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(SAEnum(FavoriteTargetType), nullable=False)
    bicycle_id = Column(Integer, ForeignKey("bicycle.id", ondelete="SET NULL"), nullable=True)
    station_name = Column(String(100), nullable=True)
    nickname = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("UnifiedUser", backref="favorites")
    bicycle = relationship("Bicycle", backref="favorites")


class PenaltyStrike(Base):
    __tablename__ = "penalty_strike"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_unifieduser.id", ondelete="CASCADE"), nullable=False)
    reason = Column(SAEnum(PenaltyReason), nullable=False)
    penalty_points = Column(Integer, default=1)
    action = Column(String(20), default="warning")
    suspension_days = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("UnifiedUser", backref="penalties")


class LostItem(Base):
    __tablename__ = "lost_item"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_unifieduser.id", ondelete="CASCADE"), nullable=False)
    bicycle_id = Column(Integer, ForeignKey("bicycle.id", ondelete="SET NULL"), nullable=True)
    item_name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=True)
    image_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    found_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="lost")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("UnifiedUser", backref="lost_items")
    bicycle = relationship("Bicycle", backref="lost_items")
