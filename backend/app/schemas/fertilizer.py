"""Fertilizer schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FertilizerStepOut(BaseModel):
    id: int
    step_number: int
    product_name: str
    product_description: Optional[str] = None
    season: Optional[str] = None
    month_start: Optional[int] = None
    month_end: Optional[int] = None
    application_rate_per_1k: Optional[str] = None
    coverage_sqft_per_bag: Optional[int] = None
    bag_weight: Optional[str] = None
    purpose: Optional[str] = None
    tips: Optional[str] = None
    icon_emoji: str = "🧪"

    class Config:
        from_attributes = True


class FertilizerProgramOut(BaseModel):
    id: int
    name: str
    slug: str
    brand: Optional[str] = None
    description: Optional[str] = None
    grass_season: Optional[str] = None
    soil_type: Optional[str] = None
    is_builtin: bool = False
    is_custom: bool = False
    step_count: int = 0
    year: Optional[int] = None
    steps: List[FertilizerStepOut] = []

    class Config:
        from_attributes = True


class FertilizerApplicationOut(BaseModel):
    id: int
    step_id: int
    year: int
    scheduled_date: Optional[datetime] = None
    applied_date: Optional[datetime] = None
    status: str = "pending"
    notes: Optional[str] = None
    product_used: Optional[str] = None

    class Config:
        from_attributes = True


class CustomProgramCreate(BaseModel):
    name: str
    description: Optional[str] = None
    grass_season: str = "any"
    soil_type: str = "any"


class CustomProgramUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    grass_season: Optional[str] = None
    soil_type: Optional[str] = None


class CustomStepCreate(BaseModel):
    step_number: int = 1
    product_name: str
    product_description: Optional[str] = None
    season: Optional[str] = None
    month_start: Optional[int] = None
    month_end: Optional[int] = None
    application_rate_per_1k: Optional[str] = None
    coverage_sqft_per_bag: Optional[int] = None
    bag_weight: Optional[str] = None
    purpose: Optional[str] = None
    tips: Optional[str] = None
    icon_emoji: str = "🧪"


class CustomStepUpdate(BaseModel):
    step_number: Optional[int] = None
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    season: Optional[str] = None
    month_start: Optional[int] = None
    month_end: Optional[int] = None
    application_rate_per_1k: Optional[str] = None
    coverage_sqft_per_bag: Optional[int] = None
    bag_weight: Optional[str] = None
    purpose: Optional[str] = None
    tips: Optional[str] = None
    icon_emoji: Optional[str] = None


class ApplyStepRequest(BaseModel):
    status: str = "done"  # done or skipped
    notes: Optional[str] = None
    product_used: Optional[str] = None
    applied_date: Optional[datetime] = None
