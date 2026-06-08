"""Fertilizer program models — programs, steps, and application tracking."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class FertilizerProgram(Base):
    """A named fertilizer program (built-in brand or custom)."""
    __tablename__ = "fertilizer_program"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    brand = Column(String(100))  # "Scotts", "Jonathan Green", or null for custom
    description = Column(Text)
    grass_season = Column(String(20))  # cool, warm, transition, any
    soil_type = Column(String(20))  # acidic, alkaline, any, null
    is_builtin = Column(Boolean, default=False)
    is_custom = Column(Boolean, default=False)
    source_url = Column(String(500))
    year = Column(Integer)  # catalog year
    step_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    steps = relationship("FertilizerStep", back_populates="program",
                         cascade="all, delete-orphan", order_by="FertilizerStep.step_number")


class FertilizerStep(Base):
    """One step in a fertilizer program (e.g., 'Step 1: Crabgrass Preventer')."""
    __tablename__ = "fertilizer_step"

    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("fertilizer_program.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    product_name = Column(String(300), nullable=False)
    product_description = Column(Text)
    season = Column(String(30))  # early_spring, late_spring, summer, fall
    month_start = Column(Integer)  # 1-12
    month_end = Column(Integer)  # 1-12
    application_rate_per_1k = Column(String(100))  # e.g., "2.87 lbs per 1,000 sqft"
    coverage_sqft_per_bag = Column(Integer)  # e.g., 5000 or 15000
    bag_weight = Column(String(50))  # e.g., "14.29 lbs"
    purpose = Column(Text)
    tips = Column(Text)
    icon_emoji = Column(String(10), default="🧪")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    program = relationship("FertilizerProgram", back_populates="steps")
    applications = relationship("FertilizerApplication", back_populates="step",
                                cascade="all, delete-orphan")


class FertilizerApplication(Base):
    """Tracks actual application of a fertilizer step for a given year."""
    __tablename__ = "fertilizer_application"

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey("fertilizer_step.id", ondelete="CASCADE"), nullable=False)
    lawn_id = Column(Integer, ForeignKey("lawn_config.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    scheduled_date = Column(DateTime(timezone=True))
    applied_date = Column(DateTime(timezone=True))
    status = Column(String(20), default="pending")  # pending, done, skipped
    notes = Column(Text)
    product_used = Column(String(300))  # override if different product was used
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    step = relationship("FertilizerStep", back_populates="applications")
