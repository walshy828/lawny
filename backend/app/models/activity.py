"""Lawn care activity / event tracking model."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


# Valid activity types
ACTIVITY_TYPES = [
    "mow", "fertilize", "aerate", "dethatch", "water",
    "overseed", "weed_control", "pest_control", "soil_test",
    "lime", "topdress", "edge", "leaf_cleanup", "other"
]


class Activity(Base):
    """A logged lawn care activity / event."""
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("lawn_zone.id", ondelete="SET NULL"), nullable=True)  # null = whole lawn
    activity_type = Column(String(50), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    products_used = Column(JSON)  # [{name, amount, unit}, ...]
    health_score = Column(Integer)  # 1-10 visual rating
    water_amount_inches = Column(Float, nullable=True)  # inches of water applied (for 'water' activities)
    photo_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    zone = relationship("LawnZone", back_populates="activities")
