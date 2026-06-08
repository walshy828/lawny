"""Lawn configuration & geocoding API."""

import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import LawnConfig, LawnZone
from app.schemas import LawnConfigCreate, LawnConfigUpdate, LawnConfigOut, GRASS_TYPES
from app.services.weather import geocode_address

router = APIRouter(prefix="/api", tags=["lawn"])


@router.get("/lawn")
async def get_lawn(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnConfig).limit(1))
    lawn = result.scalar_one_or_none()
    if not lawn:
        return None

    zones = await db.execute(select(LawnZone).where(LawnZone.lawn_id == lawn.id))
    zone_list = zones.scalars().all()
    total_sqft = sum(z.area_sqft or 0 for z in zone_list)

    return {
        **{c.name: getattr(lawn, c.name) for c in lawn.__table__.columns},
        "total_sqft": round(total_sqft, 0),
        "zone_count": len(zone_list),
    }


@router.post("/lawn")
async def create_lawn(data: LawnConfigCreate, db: AsyncSession = Depends(get_db)):
    # Only allow one lawn for now (future: multi-lawn)
    existing = await db.execute(select(LawnConfig).limit(1))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Lawn already exists. Use PUT to update.")

    lawn = LawnConfig(**data.model_dump())
    db.add(lawn)
    await db.flush()
    return {**{c.name: getattr(lawn, c.name) for c in lawn.__table__.columns}, "total_sqft": 0, "zone_count": 0}


@router.put("/lawn")
async def update_lawn(data: LawnConfigUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnConfig).limit(1))
    lawn = result.scalar_one_or_none()
    if not lawn:
        # Auto-create if not exists
        lawn = LawnConfig()
        db.add(lawn)
        await db.flush()

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lawn, key, value)

    return {c.name: getattr(lawn, c.name) for c in lawn.__table__.columns}


@router.post("/lawn/geocode")
async def geocode(query: dict):
    address = query.get("address", "")
    if not address:
        raise HTTPException(400, "Address is required")
    result = await geocode_address(address)
    if not result:
        raise HTTPException(404, "Could not geocode address")
    return result


@router.get("/lawn/grass-types")
async def grass_types():
    return GRASS_TYPES
