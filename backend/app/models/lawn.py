"""Lawn and zone models."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class LawnConfig(Base):
    """A user's lawn / property configuration.

    Architected with an ID primary key so multi-lawn support can be added
    later by simply removing the single-lawn constraint in the API layer.
    """
    __tablename__ = "lawn_config"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, default="My Lawn")
    address = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    grass_type = Column(String(50))  # bermuda, fescue, bluegrass, zoysia, etc.
    climate_zone = Column(String(20))  # USDA zone auto-detected or manual
    active_program_id = Column(Integer, ForeignKey("fertilizer_program.id", ondelete="SET NULL"))
    ai_provider = Column(String(20), server_default="openai")  # openai, anthropic, gemini
    usda_zone = Column(String(20))
    # Per-provider API keys stored in DB (override env vars when set)
    openai_api_key = Column(String(300))
    openai_model = Column(String(100), server_default="gpt-4o")
    anthropic_api_key = Column(String(300))
    anthropic_model = Column(String(100), server_default="claude-sonnet-4-6")
    gemini_api_key = Column(String(300))
    gemini_model = Column(String(100), server_default="gemini-2.0-flash")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    zones = relationship("LawnZone", back_populates="lawn", cascade="all, delete-orphan")


class LawnZone(Base):
    """A named polygon zone within the lawn (front yard, side strip, etc.)."""
    __tablename__ = "lawn_zone"

    id = Column(Integer, primary_key=True)
    lawn_id = Column(Integer, ForeignKey("lawn_config.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    color = Column(String(9), default="#52B788")  # hex color for map overlay
    polygon_coords = Column(JSON, nullable=False)  # [{lat, lng}, ...]
    area_sqft = Column(Float, default=0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lawn = relationship("LawnConfig", back_populates="zones")
    activities = relationship("Activity", back_populates="zone", cascade="all, delete-orphan")
