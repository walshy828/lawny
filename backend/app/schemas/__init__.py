"""Lawn and zone schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Grass Type Options ────────────────────────────
GRASS_TYPES = {
    "cool_season": [
        {"value": "kentucky_bluegrass", "label": "Kentucky Bluegrass"},
        {"value": "tall_fescue", "label": "Tall Fescue"},
        {"value": "fine_fescue", "label": "Fine Fescue"},
        {"value": "perennial_ryegrass", "label": "Perennial Ryegrass"},
        {"value": "cool_mix", "label": "Cool-Season Mix"},
    ],
    "warm_season": [
        {"value": "bermuda", "label": "Bermuda"},
        {"value": "zoysia", "label": "Zoysia"},
        {"value": "st_augustine", "label": "St. Augustine"},
        {"value": "centipede", "label": "Centipede"},
        {"value": "buffalo", "label": "Buffalo"},
        {"value": "bahia", "label": "Bahia"},
        {"value": "warm_mix", "label": "Warm-Season Mix"},
    ],
    "transition": [
        {"value": "mixed_blend", "label": "Mixed / Transition Blend"},
    ],
}


class LawnConfigBase(BaseModel):
    name: str = "My Lawn"
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    grass_type: Optional[str] = None
    climate_zone: Optional[str] = None


class LawnConfigCreate(LawnConfigBase):
    pass


class LawnConfigUpdate(LawnConfigBase):
    name: Optional[str] = None


class LawnConfigOut(LawnConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_sqft: float = 0
    zone_count: int = 0

    class Config:
        from_attributes = True


class LawnZoneBase(BaseModel):
    name: str
    color: str = "#52B788"
    polygon_coords: list  # [{lat: float, lng: float}, ...]
    notes: Optional[str] = None


class LawnZoneCreate(LawnZoneBase):
    pass


class LawnZoneUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    polygon_coords: Optional[list] = None
    notes: Optional[str] = None


class LawnZoneOut(LawnZoneBase):
    id: int
    lawn_id: int
    area_sqft: float
    created_at: datetime

    class Config:
        from_attributes = True
