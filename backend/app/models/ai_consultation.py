"""AI consultation history — stores questions and AI responses with context snapshots."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class AIConsultation(Base):
    """Stores AI lawn consultation requests and responses."""
    __tablename__ = "ai_consultation"

    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    context_snapshot = Column(JSON)         # lawn context bundle sent to AI
    response_text = Column(Text)            # raw AI text response
    structured_response = Column(JSON)      # parsed recommendations if applicable
    ai_provider = Column(String(20))        # openai, anthropic, gemini
    ai_model = Column(String(50))
    observation_ids = Column(JSON)          # observation IDs that were context
    zone_id = Column(Integer, ForeignKey("lawn_zone.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
