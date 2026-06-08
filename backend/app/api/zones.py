"""Lawn zones API — CRUD and area calculation."""

import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import LawnConfig, LawnZone
from app.schemas import LawnZoneCreate, LawnZoneUpdate

router = APIRouter(prefix="/api", tags=["zones"])


def calculate_polygon_area_sqft(coords: list) -> float:
    """Calculate area of a polygon defined by lat/lng points using the Shoelace formula.

    Converts geographic coordinates to approximate feet first, then computes area.
    """
    if not coords or len(coords) < 3:
        return 0

    # Use the centroid to compute local scale factors
    avg_lat = sum(p.get("lat", 0) for p in coords) / len(coords)
    lat_rad = math.radians(avg_lat)

    # Meters per degree at this latitude
    m_per_deg_lat = 111132.92
    m_per_deg_lng = 111412.84 * math.cos(lat_rad)

    # Convert to feet (local coordinate system)
    ft_per_m = 3.28084
    points_ft = []
    for p in coords:
        x = p.get("lng", 0) * m_per_deg_lng * ft_per_m
        y = p.get("lat", 0) * m_per_deg_lat * ft_per_m
        points_ft.append((x, y))

    # Shoelace formula
    n = len(points_ft)
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += points_ft[i][0] * points_ft[j][1]
        area -= points_ft[j][0] * points_ft[i][1]

    return abs(area) / 2


@router.get("/zones")
async def list_zones(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnZone).order_by(LawnZone.name))
    zones = result.scalars().all()
    return [{
        **{c.name: getattr(z, c.name) for c in z.__table__.columns},
    } for z in zones]


@router.post("/zones")
async def create_zone(data: LawnZoneCreate, db: AsyncSession = Depends(get_db)):
    # Get the lawn (auto-create if needed)
    result = await db.execute(select(LawnConfig).limit(1))
    lawn = result.scalar_one_or_none()
    if not lawn:
        lawn = LawnConfig(name="My Lawn")
        db.add(lawn)
        await db.flush()

    area = calculate_polygon_area_sqft(data.polygon_coords)
    zone = LawnZone(lawn_id=lawn.id, area_sqft=round(area, 1), **data.model_dump())
    db.add(zone)
    await db.flush()
    return {c.name: getattr(zone, c.name) for c in zone.__table__.columns}


@router.put("/zones/{zone_id}")
async def update_zone(zone_id: int, data: LawnZoneUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnZone).where(LawnZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(404, "Zone not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(zone, key, value)

    # Recalculate area if polygon changed
    if data.polygon_coords:
        zone.area_sqft = round(calculate_polygon_area_sqft(data.polygon_coords), 1)

    return {c.name: getattr(zone, c.name) for c in zone.__table__.columns}


@router.delete("/zones/{zone_id}")
async def delete_zone(zone_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnZone).where(LawnZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(404, "Zone not found")
    await db.delete(zone)
    return {"ok": True}
