"""Schedule schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScheduleBase(BaseModel):
    activity_type: str
    frequency_days: int = 7
    zone_id: Optional[int] = None
    notes: Optional[str] = None
    is_active: bool = True


class ScheduleCreate(ScheduleBase):
    next_due: Optional[datetime] = None


class ScheduleUpdate(BaseModel):
    activity_type: Optional[str] = None
    frequency_days: Optional[int] = None
    zone_id: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduleOut(ScheduleBase):
    id: int
    last_completed: Optional[datetime] = None
    next_due: Optional[datetime] = None
    zone_name: Optional[str] = None
    is_overdue: bool = False
    days_until_due: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
