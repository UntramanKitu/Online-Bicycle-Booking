from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from database import Base


# ==================== ENUM Types ====================
class FavoriteTargetType(str, enum.Enum):
    BICYCLE = "bicycle"
    STATION = "station"


class PenaltyReason(str, enum.Enum):
    LATE_RETURN = "late_return"
    DAMAGED = "damaged"
    LOST = "lost"
    OTHER = "other"


class PointsReason(str, enum.Enum):
    LATE_RETURN = "late_return"
    DAMAGED = "damaged"
    LOST = "lost"
    GOOD_RETURN = "good_return"
    COMMUNITY_SERVICE = "community_service"
    REPORT = "report"
    WEEKLY_BONUS = "weekly_bonus"
    OTHER = "other"


# ==================== Shared stub tables (FK reference เท่านั้น) ====================

class UnifiedUser(Base):
    __tablename__ = "unified_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    points = Column(Integer, default=12)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Bicycle(Base):
    __tablename__ = "bicycle"

    id = Column(Integer, primary_key=True, index=True)
    bike_code = Column(String(50), unique=True, nullable=False, index=True)
    brand = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    color = Column(String(30), nullable=True)
    status = Column(String(20), default="available")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ==================== 1. รายการโปรด ====================

class Favorite(Base):
    __tablename__ = "favorite"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("unified_user.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(SAEnum(FavoriteTargetType), nullable=False)
    bicycle_id = Column(Integer, ForeignKey("bicycle.id", ondelete="SET NULL"), nullable=True)
    station_name = Column(String(100), nullable=True)
    nickname = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("UnifiedUser", backref="favorites")
    bicycle = relationship("Bicycle", backref="favorites")


# ==================== 2. บทลงโทษ ====================

class PenaltyStrike(Base):
    __tablename__ = "penalty_strike"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("unified_user.id", ondelete="CASCADE"), nullable=False)
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


# ==================== ประวัติแต้ม ====================

class PointsLog(Base):
    __tablename__ = "points_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("unified_user.id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False)
    reason = Column(SAEnum(PointsReason), nullable=False)
    description = Column(Text, nullable=True)
    penalty_id = Column(Integer, ForeignKey("penalty_strike.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("UnifiedUser", backref="points_logs")


# ==================== 3. ของหาย ====================

class LostItem(Base):
    __tablename__ = "lost_item"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("unified_user.id", ondelete="CASCADE"), nullable=False)
    bicycle_id = Column(Integer, ForeignKey("bicycle.id", ondelete="CASCADE"), nullable=False)
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