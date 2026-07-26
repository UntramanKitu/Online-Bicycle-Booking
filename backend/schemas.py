from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# ===== Return Record =====
class ReturnRecordBase(BaseModel):
    bike_id: str
    user_id: str
    return_time: datetime
    station: str
    status: str = "on_time"
    notes: Optional[str] = None


class ReturnRecordCreate(ReturnRecordBase):
    pass


class ReturnRecordUpdate(BaseModel):
    bike_id: Optional[str] = None
    user_id: Optional[str] = None
    return_time: Optional[datetime] = None
    station: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ReturnRecordResponse(ReturnRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===== Damage Evidence =====
class DamageEvidenceBase(BaseModel):
    return_id: int
    description: str
    severity: str = "minor"


class DamageEvidenceCreate(DamageEvidenceBase):
    pass


class DamageEvidenceUpdate(BaseModel):
    description: Optional[str] = None
    severity: Optional[str] = None


class DamageEvidenceResponse(DamageEvidenceBase):
    id: int
    image_paths: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===== Favorite =====
class FavoriteBase(BaseModel):
    user_id: str
    favorite_type: str
    favorite_id: str
    nickname: Optional[str] = None


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteUpdate(BaseModel):
    nickname: Optional[str] = None


class FavoriteResponse(FavoriteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
