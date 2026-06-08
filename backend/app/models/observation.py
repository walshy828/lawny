"""Observation model — structured log of what the user sees in their lawn."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


OBSERVATION_TYPES = [
    "weed_pressure", "clover", "moss", "crabgrass", "nutsedge", "dandelion",
    "bare_spots", "brown_patch", "dollar_spot", "grub_damage", "thatch",
    "compaction", "insect", "fungus", "discoloration", "other",
]

OBSERVATION_TYPE_META = {
    "weed_pressure":  {"icon": "🌿", "label": "General Weeds"},
    "clover":         {"icon": "☘️", "label": "Clover"},
    "moss":           {"icon": "🟢", "label": "Moss"},
    "crabgrass":      {"icon": "🌾", "label": "Crabgrass"},
    "nutsedge":       {"icon": "🎋", "label": "Nutsedge"},
    "dandelion":      {"icon": "🌼", "label": "Dandelion"},
    "bare_spots":     {"icon": "🟫", "label": "Bare Spots"},
    "brown_patch":    {"icon": "🍂", "label": "Brown Patch"},
    "dollar_spot":    {"icon": "💰", "label": "Dollar Spot"},
    "grub_damage":    {"icon": "🪱", "label": "Grub Damage"},
    "thatch":         {"icon": "🪹", "label": "Thatch"},
    "compaction":     {"icon": "🧱", "label": "Compaction"},
    "insect":         {"icon": "🐛", "label": "Insects"},
    "fungus":         {"icon": "🍄", "label": "Fungus"},
    "discoloration":  {"icon": "🟡", "label": "Discoloration"},
    "other":          {"icon": "📝", "label": "Other"},
}


class Observation(Base):
    """A user-logged observation about their lawn's condition."""
    __tablename__ = "observation"

    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("lawn_zone.id", ondelete="SET NULL"), nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    observation_type = Column(String(50), nullable=False)
    severity = Column(String(20))         # low, moderate, severe
    coverage_pct = Column(Integer)        # 0-100, how much of the zone/lawn is affected
    description = Column(Text)
    photo_url = Column(String(500))
    status = Column(String(20), server_default="active")  # active, monitoring, resolved
    resolved_date = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
