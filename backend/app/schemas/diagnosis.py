"""Diagnosis schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DiagnosisIssue(BaseModel):
    name: str
    type: str  # weed, disease, pest, nutrient, other
    severity: str  # low, moderate, severe
    confidence: float  # 0-1


class DiagnosisProduct(BaseModel):
    name: str
    type: str  # herbicide, fungicide, fertilizer, etc.
    application_rate: Optional[str] = None
    timing: Optional[str] = None
    notes: Optional[str] = None


class DiagnosisAction(BaseModel):
    action: str
    priority: str  # immediate, soon, preventive
    details: Optional[str] = None


class DiagnosisResultOut(BaseModel):
    id: int
    zone_id: Optional[int] = None
    photo_url: str
    issues: list[DiagnosisIssue] = []
    products: list[DiagnosisProduct] = []
    actions: list[DiagnosisAction] = []
    summary: str = ""
    ai_model_used: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
