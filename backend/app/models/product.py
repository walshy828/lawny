"""Product catalog model — built-in and custom lawn care products."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.models.base import Base


PRODUCT_CATEGORIES = [
    "fertilizer", "pre_emergent", "post_emergent", "herbicide",
    "fungicide", "insecticide", "soil_amendment", "seed", "other",
]


class ProductCatalog(Base):
    """A lawn care product, either from the built-in catalog or user-created."""
    __tablename__ = "product_catalog"

    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    brand = Column(String(100))
    category = Column(String(50))               # see PRODUCT_CATEGORIES
    npk_ratio = Column(String(20))              # e.g., "32-0-10"
    active_ingredient = Column(String(300))
    application_rate_per_1k = Column(String(100))
    coverage_sqft_per_bag = Column(Integer)
    bag_size = Column(String(50))
    safe_grass_types = Column(JSON)             # null = safe for all grass types
    application_timing = Column(Text)
    notes = Column(Text)
    is_builtin = Column(Boolean, server_default="false")
    is_custom = Column(Boolean, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
