"""Weather, drought, and watering recommendation models."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class WeatherSnapshot(Base):
    """Hourly/daily weather data cached from Open-Meteo."""
    __tablename__ = "weather_snapshot"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), nullable=False, unique=True)
    temp_high_f = Column(Float)
    temp_low_f = Column(Float)
    soil_temp_0cm_f = Column(Float)  # surface soil temp
    soil_temp_6cm_f = Column(Float)  # ~2.5 inch depth
    precipitation_in = Column(Float)  # inches
    humidity_pct = Column(Float)
    wind_speed_mph = Column(Float)
    uv_index = Column(Float)
    sunshine_hours = Column(Float)
    weather_code = Column(Integer)
    raw_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DroughtStatus(Base):
    """USDM drought status snapshots."""
    __tablename__ = "drought_status"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), nullable=False)
    drought_level = Column(String(10))  # None, D0, D1, D2, D3, D4
    drought_label = Column(String(50))  # Abnormally Dry, Moderate, Severe, Extreme, Exceptional
    coverage_pct = Column(Float)
    source_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WateringRecommendation(Base):
    """Daily AI-generated watering recommendations."""
    __tablename__ = "watering_recommendation"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), nullable=False, unique=True)
    recommendation = Column(String(20))  # none, light, moderate, heavy
    frequency = Column(String(50))  # "every 2 days", "daily AM", "twice daily"
    duration_minutes = Column(Integer)  # suggested sprinkler run time
    reasoning = Column(Text)
    rain_past_7d_in = Column(Float)
    rain_forecast_7d_in = Column(Float)
    soil_temp_f = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
