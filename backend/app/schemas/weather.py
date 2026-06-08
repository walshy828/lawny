"""Weather and recommendation schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CurrentWeatherOut(BaseModel):
    temperature_f: Optional[float] = None
    feels_like_f: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    precipitation_in: Optional[float] = None
    uv_index: Optional[float] = None
    soil_temp_surface_f: Optional[float] = None
    soil_temp_6cm_f: Optional[float] = None
    sunshine_hours: Optional[float] = None
    weather_code: Optional[int] = None
    weather_description: str = ""
    timestamp: Optional[datetime] = None


class ForecastDayOut(BaseModel):
    date: str
    temp_high_f: Optional[float] = None
    temp_low_f: Optional[float] = None
    precipitation_in: Optional[float] = None
    precipitation_probability: Optional[int] = None
    weather_code: Optional[int] = None
    weather_description: str = ""
    sunshine_hours: Optional[float] = None
    uv_index_max: Optional[float] = None


class ForecastOut(BaseModel):
    days: list[ForecastDayOut] = []
    total_precipitation_7d_in: float = 0


class DroughtStatusOut(BaseModel):
    drought_level: Optional[str] = None
    drought_label: str = "No Data"
    coverage_pct: Optional[float] = None
    last_updated: Optional[datetime] = None
    severity_color: str = "#52B788"


class WateringRecommendationOut(BaseModel):
    recommendation: str = "unknown"  # none, light, moderate, heavy
    frequency: str = ""
    duration_minutes: Optional[int] = None
    reasoning: str = ""
    rain_past_7d_in: Optional[float] = None
    rain_forecast_7d_in: Optional[float] = None
    soil_temp_f: Optional[float] = None
    drought_status: Optional[str] = None
    date: Optional[datetime] = None
