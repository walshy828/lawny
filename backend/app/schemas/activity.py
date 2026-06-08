"""Activity schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ActivityBase(BaseModel):
    zone_id: Optional[int] = None
    activity_type: str
    date: Optional[datetime] = None
    notes: Optional[str] = None
    products_used: Optional[list] = None
    health_score: Optional[int] = Field(None, ge=1, le=10)
    water_amount_inches: Optional[float] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    zone_id: Optional[int] = None
    activity_type: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None
    products_used: Optional[list] = None
    health_score: Optional[int] = Field(None, ge=1, le=10)
    water_amount_inches: Optional[float] = None


class ActivityOut(ActivityBase):
    id: int
    zone_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityStatsOut(BaseModel):
    total_activities: int = 0
    last_mow: Optional[datetime] = None
    days_since_mow: Optional[int] = None
    last_fertilize: Optional[datetime] = None
    days_since_fertilize: Optional[int] = None
    avg_health_score: Optional[float] = None
    health_trend: list = []  # [{date, score}]
    activity_counts: dict = {}  # {mow: 12, fertilize: 3, ...}
