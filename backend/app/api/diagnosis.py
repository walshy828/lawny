"""AI Lawn Diagnosis API — multi-provider photo analysis."""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from app.database import get_db
from app.models import LawnDiagnosis, LawnConfig
from app.services.ai_provider import get_provider, db_config_from_lawn
from app.config import settings

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])
UPLOAD_DIR = "/app/uploads/diagnosis"


@router.post("/analyze")
async def analyze(
    photo: UploadFile = File(...),
    zone_id: Optional[int] = Form(None),
    ai_provider: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    # Save uploaded photo
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(photo.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await photo.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Determine which provider to use (DB key takes priority over env)
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()

    selected_provider = ai_provider or (lawn.ai_provider if lawn else None) or "openai"
    provider = get_provider(selected_provider, db_config=db_config_from_lawn(lawn))

    # Build user message with lawn context
    context_parts = []
    if lawn:
        if lawn.grass_type:
            context_parts.append(f"Grass type: {lawn.grass_type}")
        if lawn.address:
            context_parts.append(f"Location: {lawn.address}")

    user_message = "Please analyze this lawn photo and identify any issues."
    if context_parts:
        user_message += "\n\nContext:\n" + "\n".join(context_parts)

    try:
        result = await provider.analyze_photo(filepath, user_message)
    except Exception as e:
        raise HTTPException(500, f"AI analysis failed: {str(e)}")

    # Save to database
    diagnosis = LawnDiagnosis(
        zone_id=zone_id,
        photo_path=f"/uploads/diagnosis/{filename}",
        analysis_result={"issues": result.get("issues", [])},
        recommendations={"products": result.get("products", []), "actions": result.get("actions", [])},
        ai_model_used=result.get("ai_model_used"),
    )
    db.add(diagnosis)
    await db.flush()

    return {
        "id": diagnosis.id,
        "photo_url": diagnosis.photo_path,
        "summary": result.get("summary", ""),
        "issues": result.get("issues", []),
        "products": result.get("products", []),
        "actions": result.get("actions", []),
        "ai_model_used": result.get("ai_model_used"),
        "ai_provider": provider.provider_name,
    }


@router.get("/history")
async def diagnosis_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LawnDiagnosis).order_by(desc(LawnDiagnosis.created_at)).limit(limit)
    )
    items = []
    for d in result.scalars().all():
        issues = d.analysis_result.get("issues", []) if d.analysis_result else []
        items.append({
            "id": d.id,
            "photo_url": d.photo_path,
            "issue_count": len(issues),
            "summary": issues[0].get("name", "No issues") if issues else "Healthy",
            "ai_model_used": d.ai_model_used,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })
    return items


@router.get("/{diagnosis_id}")
async def get_diagnosis(diagnosis_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnDiagnosis).where(LawnDiagnosis.id == diagnosis_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(404, "Diagnosis not found")

    return {
        "id": d.id,
        "zone_id": d.zone_id,
        "photo_url": d.photo_path,
        "issues": d.analysis_result.get("issues", []) if d.analysis_result else [],
        "products": d.recommendations.get("products", []) if d.recommendations else [],
        "actions": d.recommendations.get("actions", []) if d.recommendations else [],
        "ai_model_used": d.ai_model_used,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }
