"""Soil test model — tracks nutrient levels and pH over time per zone."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class SoilTest(Base):
    __tablename__ = "soil_test"

    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("lawn_zone.id", ondelete="SET NULL"), nullable=True)
    test_date = Column(DateTime(timezone=True), nullable=False)
    lab_name = Column(String(200))

    # pH
    ph = Column(Float)
    buffer_ph = Column(Float)  # Penn State method — used for precise lime calculation

    # Macronutrients (ppm)
    nitrogen_ppm = Column(Float)
    phosphorus_ppm = Column(Float)
    potassium_ppm = Column(Float)

    # Secondary nutrients (ppm)
    calcium_ppm = Column(Float)
    magnesium_ppm = Column(Float)
    sulfur_ppm = Column(Float)

    # Soil health
    organic_matter_pct = Column(Float)
    cec = Column(Float)  # Cation Exchange Capacity (meq/100g)

    # Lab lime recommendation (optional — labs often include this)
    lime_recommendation_lbs_per_1k = Column(Float)

    notes = Column(Text)
    raw_data = Column(JSON)  # store any extra lab fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
