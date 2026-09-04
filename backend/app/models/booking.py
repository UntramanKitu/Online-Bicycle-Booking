from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func
from app.database import Base


class ReservationBooking(Base):
    __tablename__ = "reservation_booking"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    bicycle_id = Column(Integer, nullable=False)
    booking_type = Column(ENUM("advance_reservation", "walk_in", name="booking_type", create_type=True), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(ENUM(
        "pending", "confirmed", "in_progress", "completed", "cancelled", "no_show",
        name="booking_status", create_type=True
    ), nullable=False, default="pending")
    pickup_location = Column(String(255), nullable=True)
    return_location = Column(String(255), nullable=True)
    checked_out_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UsageHistoryLog(Base):
    __tablename__ = "usage_history_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    bicycle_id = Column(Integer, nullable=False)
    booking_id = Column(Integer, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    distance_km = Column(Numeric(10, 2), nullable=True)
    starting_station = Column(String(255), nullable=True)
    ending_station = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SupportTicket(Base):
    __tablename__ = "support_ticket"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    assigned_to = Column(Integer, nullable=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(ENUM(
        "bicycle_issue", "account_issue", "booking_issue", "other",
        name="ticket_category", create_type=True
    ), nullable=False)
    priority = Column(ENUM(
        "low", "normal", "high", "urgent",
        name="ticket_priority", create_type=True
    ), nullable=False, default="normal")
    status = Column(ENUM(
        "open", "in_progress", "resolved", "closed", "reopened",
        name="ticket_status", create_type=True
    ), nullable=False, default="open")
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)