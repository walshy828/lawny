"""AI lawn diagnosis model."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class LawnDiagnosis(Base):
    """Stores AI-powered lawn photo analysis results."""
    __tablename__ = "lawn_diagnosis"

    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("lawn_zone.id", ondelete="SET NULL"), nullable=True)
    photo_path = Column(String(500), nullable=False)
    analysis_result = Column(JSON)  # {issues: [{name, type, severity, confidence}]}
    recommendations = Column(JSON)  # {products: [], actions: []}
    ai_model_used = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
