from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ==================== ReservationBooking ====================
class ReservationBookingCreate(BaseModel):
    user_id: int
    bicycle_id: int
    booking_type: str
    start_time: datetime
    end_time: datetime
    pickup_location: Optional[str] = None
    return_location: Optional[str] = None


class ReservationBookingUpdate(BaseModel):
    booking_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    pickup_location: Optional[str] = None
    return_location: Optional[str] = None
    checked_out_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None


class ReservationBookingResponse(BaseModel):
    id: int
    user_id: int
    bicycle_id: int
    booking_type: str
    start_time: datetime
    end_time: datetime
    status: str
    pickup_location: Optional[str] = None
    return_location: Optional[str] = None
    checked_out_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==================== UsageHistoryLog ====================
class UsageHistoryLogCreate(BaseModel):
    user_id: int
    bicycle_id: int
    booking_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    starting_station: Optional[str] = None
    ending_station: Optional[str] = None
    status: Optional[str] = None


class UsageHistoryLogUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    ending_station: Optional[str] = None
    status: Optional[str] = None


class UsageHistoryLogResponse(BaseModel):
    id: int
    user_id: int
    bicycle_id: int
    booking_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    starting_station: Optional[str] = None
    ending_station: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== SupportTicket ====================
class SupportTicketCreate(BaseModel):
    user_id: int
    subject: str
    description: str
    category: str
    priority: Optional[str] = "normal"


class SupportTicketUpdate(BaseModel):
    assigned_to: Optional[int] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None


class SupportTicketResponse(BaseModel):
    id: int
    user_id: int
    assigned_to: Optional[int] = None
    subject: str
    description: str
    category: str
    priority: str
    status: str
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}