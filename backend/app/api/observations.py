"""Observations API — log and track lawn condition observations."""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Observation, LawnZone, OBSERVATION_TYPES, OBSERVATION_TYPE_META

router = APIRouter(prefix="/api/observations", tags=["observations"])
UPLOAD_DIR = "/app/uploads/observations"


def _obs_dict(o: Observation, zone_name: Optional[str] = None) -> dict:
    meta = OBSERVATION_TYPE_META.get(o.observation_type, {"icon": "📝", "label": o.observation_type})
    return {
        "id": o.id,
        "zone_id": o.zone_id,
        "zone_name": zone_name,
        "date": o.date.isoformat() if o.date else None,
        "observation_type": o.observation_type,
        "type_icon": meta["icon"],
        "type_label": meta["label"],
        "severity": o.severity,
        "coverage_pct": o.coverage_pct,
        "description": o.description,
        "photo_url": o.photo_url,
        "status": o.status,
        "resolved_date": o.resolved_date.isoformat() if o.resolved_date else None,
        "resolution_notes": o.resolution_notes,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
    }


@router.get("/types")
async def get_observation_types():
    return [
        {"value": t, "icon": OBSERVATION_TYPE_META[t]["icon"], "label": OBSERVATION_TYPE_META[t]["label"]}
        for t in OBSERVATION_TYPES
    ]


@router.get("")
async def list_observations(
    status: Optional[str] = None,
    zone_id: Optional[int] = None,
    obs_type: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Observation).order_by(desc(Observation.date))
    if status:
        q = q.where(Observation.status == status)
    if zone_id:
        q = q.where(Observation.zone_id == zone_id)
    if obs_type:
        q = q.where(Observation.observation_type == obs_type)
    q = q.limit(limit)

    result = await db.execute(q)
    items = []
    for o in result.scalars().all():
        zone_name = None
        if o.zone_id:
            zr = await db.execute(select(LawnZone.name).where(LawnZone.id == o.zone_id))
            zone_name = zr.scalar_one_or_none()
        items.append(_obs_dict(o, zone_name))
    return items


@router.post("")
async def create_observation(data: dict, db: AsyncSession = Depends(get_db)):
    if data.get("observation_type") not in OBSERVATION_TYPES:
        raise HTTPException(400, f"Invalid observation_type. Valid: {OBSERVATION_TYPES}")

    date = data.get("date")
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            date = datetime.now()

    obs = Observation(
        zone_id=data.get("zone_id"),
        date=date or datetime.now(),
        observation_type=data["observation_type"],
        severity=data.get("severity"),
        coverage_pct=data.get("coverage_pct"),
        description=data.get("description"),
        photo_url=data.get("photo_url"),
        status=data.get("status", "active"),
    )
    db.add(obs)
    await db.flush()
    return _obs_dict(obs)


@router.post("/with-photo")
async def create_observation_with_photo(
    observation_type: str = Form(...),
    severity: Optional[str] = Form(None),
    coverage_pct: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    zone_id: Optional[int] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    if observation_type not in OBSERVATION_TYPES:
        raise HTTPException(400, f"Invalid observation_type")

    photo_url = None
    if photo and photo.filename:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(photo.filename)[1] or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        content = await photo.read()
        with open(filepath, "wb") as f:
            f.write(content)
        photo_url = f"/uploads/observations/{filename}"

    obs = Observation(
        zone_id=zone_id,
        date=datetime.now(),
        observation_type=observation_type,
        severity=severity,
        coverage_pct=coverage_pct,
        description=description,
        photo_url=photo_url,
        status="active",
    )
    db.add(obs)
    await db.flush()
    return _obs_dict(obs)


@router.get("/{obs_id}")
async def get_observation(obs_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Observation).where(Observation.id == obs_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Observation not found")

    zone_name = None
    if o.zone_id:
        zr = await db.execute(select(LawnZone.name).where(LawnZone.id == o.zone_id))
        zone_name = zr.scalar_one_or_none()
    return _obs_dict(o, zone_name)


@router.put("/{obs_id}")
async def update_observation(obs_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Observation).where(Observation.id == obs_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Observation not found")

    for key in ["zone_id", "observation_type", "severity", "coverage_pct", "description",
                "photo_url", "status", "resolution_notes"]:
        if key in data:
            setattr(o, key, data[key])

    if "date" in data:
        try:
            o.date = datetime.fromisoformat(data["date"])
        except (ValueError, TypeError):
            pass

    return _obs_dict(o)


@router.post("/{obs_id}/resolve")
async def resolve_observation(obs_id: int, data: dict = {}, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Observation).where(Observation.id == obs_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Observation not found")

    o.status = "resolved"
    o.resolved_date = datetime.now()
    o.resolution_notes = data.get("resolution_notes") or o.resolution_notes
    return _obs_dict(o)


@router.delete("/{obs_id}")
async def delete_observation(obs_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Observation).where(Observation.id == obs_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Observation not found")
    await db.delete(o)
    return {"ok": True}
