from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Union


class FavoriteBase(BaseModel):
    user_id: Union[int, str]
    target_type: str
    bicycle_id: Optional[Union[int, str]] = None
    station_name: Optional[str] = None
    nickname: Optional[str] = None


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteUpdate(BaseModel):
    nickname: Optional[str] = None


class FavoriteResponse(FavoriteBase):
    id: int
    user_id: int
    bicycle_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PenaltyStrikeBase(BaseModel):
    user_id: Union[int, str]
    reason: str
    penalty_points: int = Field(default=1, gt=0, le=1)
    action: str = "warning"
    suspension_days: Optional[int] = None
    description: Optional[str] = None
    completed: bool = False
    issued_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PenaltyStrikeCreate(PenaltyStrikeBase):
    pass


class PenaltyStrikeUpdate(BaseModel):
    reason: Optional[str] = None
    penalty_points: Optional[int] = Field(default=None, gt=0, le=1)
    action: Optional[str] = None
    suspension_days: Optional[int] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    completed_at: Optional[datetime] = None


class PenaltyStrikeResponse(PenaltyStrikeBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LostItemBase(BaseModel):
    user_id: Union[int, str]
    bicycle_id: Optional[Union[int, str]] = None
    item_name: str
    location: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    reported_at: Optional[datetime] = None
    found_at: Optional[datetime] = None
    status: str = "lost"


class LostItemCreate(LostItemBase):
    pass


class LostItemUpdate(BaseModel):
    item_name: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    found_at: Optional[datetime] = None
    status: Optional[str] = None


class LostItemResponse(LostItemBase):
    id: int
    user_id: int
    bicycle_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
