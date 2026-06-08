from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from app.models.base import Base


class LawnProgram(Base):
    __tablename__ = "lawn_program"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    season_year = Column(Integer)
    status = Column(String(20), server_default="active")   # active, draft, archived
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LawnProgramStep(Base):
    __tablename__ = "lawn_program_step"

    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("lawn_program.id", ondelete="CASCADE"), nullable=False)

    # Timing
    month = Column(Integer)             # 1-12
    week_of_month = Column(Integer)     # 1-4, nullable = anytime that month

    # What to do
    activity_type = Column(String(50))
    product_name = Column(String(300))
    application_rate = Column(String(200))
    notes = Column(Text)

    # Meta
    priority = Column(String(20), server_default="medium")  # critical, high, medium, low
    status = Column(String(20), server_default="pending")   # pending, done, skipped
    source = Column(String(20))         # fertilizer, ai_remediation, manual
    source_ref_id = Column(Integer)     # ID of fertilizer step or remediation action (soft ref)
    conflicts_with = Column(JSON)       # list of activity_types that conflict in same window
    order_index = Column(Integer, default=0)
    completed_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
