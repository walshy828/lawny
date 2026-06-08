from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from app.models.base import Base


class LawnAssessment(Base):
    __tablename__ = "lawn_assessment"

    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("lawn_zone.id", ondelete="SET NULL"), nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    overall_condition = Column(String(20))      # excellent, good, fair, poor
    grass_coverage_pct = Column(Integer)        # 0-100, how much area is actual grass
    notes = Column(Text)
    ai_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AssessmentFinding(Base):
    __tablename__ = "assessment_finding"

    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("lawn_assessment.id", ondelete="CASCADE"), nullable=False)
    finding_type = Column(String(50), nullable=False)   # reuses OBSERVATION_TYPES values
    severity = Column(String(20))                       # low, moderate, severe
    coverage_pct = Column(Integer)                      # 0-100
    location_notes = Column(String(300))                # "along fence", "shady areas", etc.
    photo_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RemediationPlan(Base):
    """AI-generated remediation plan produced by analyzing a LawnAssessment."""
    __tablename__ = "remediation_plan"

    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("lawn_assessment.id", ondelete="CASCADE"), nullable=False)
    findings_summary = Column(Text)
    action_steps = Column(JSON)         # list of action dicts (see _build_action_step)
    key_warnings = Column(JSON)         # list of warning strings
    expected_outcomes = Column(JSON)    # list of {finding_type, resolution, timeline}
    seasonal_context = Column(Text)
    ai_provider = Column(String(20))
    ai_model = Column(String(100))
    raw_response = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
