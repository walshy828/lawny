"""Maintenance schedule models."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class MaintenanceSchedule(Base):
    """A recurring maintenance schedule for a specific activity type."""
    __tablename__ = "maintenance_schedule"

    id = Column(Integer, primary_key=True)
    activity_type = Column(String(50), nullable=False)
    frequency_days = Column(Integer, nullable=False, default=7)
    zone_id = Column(Integer, ForeignKey("lawn_zone.id", ondelete="SET NULL"), nullable=True)
    last_completed = Column(DateTime(timezone=True))
    next_due = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
