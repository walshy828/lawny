"""Soil test API — log, list, interpret, and calculate amendments."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import SoilTest, LawnZone, LawnConfig
from app.services.soil_calculator import interpret_soil_test, calculate_lime_needed, calculate_sulfur_needed

router = APIRouter(prefix="/api/soil-tests", tags=["soil-tests"])


def _soil_test_dict(t: SoilTest, zone_name: Optional[str] = None) -> dict:
    return {
        "id": t.id,
        "zone_id": t.zone_id,
        "zone_name": zone_name,
        "test_date": t.test_date.isoformat() if t.test_date else None,
        "lab_name": t.lab_name,
        "ph": t.ph,
        "buffer_ph": t.buffer_ph,
        "nitrogen_ppm": t.nitrogen_ppm,
        "phosphorus_ppm": t.phosphorus_ppm,
        "potassium_ppm": t.potassium_ppm,
        "calcium_ppm": t.calcium_ppm,
        "magnesium_ppm": t.magnesium_ppm,
        "sulfur_ppm": t.sulfur_ppm,
        "organic_matter_pct": t.organic_matter_pct,
        "cec": t.cec,
        "lime_recommendation_lbs_per_1k": t.lime_recommendation_lbs_per_1k,
        "notes": t.notes,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("")
async def list_soil_tests(
    zone_id: Optional[int] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(SoilTest).order_by(desc(SoilTest.test_date))
    if zone_id:
        q = q.where(SoilTest.zone_id == zone_id)
    q = q.limit(limit)

    result = await db.execute(q)
    items = []
    for t in result.scalars().all():
        zone_name = None
        if t.zone_id:
            zr = await db.execute(select(LawnZone.name).where(LawnZone.id == t.zone_id))
            zone_name = zr.scalar_one_or_none()
        items.append(_soil_test_dict(t, zone_name))
    return items


@router.post("")
async def create_soil_test(data: dict, db: AsyncSession = Depends(get_db)):
    test_date = data.pop("test_date", None)
    if isinstance(test_date, str):
        try:
            test_date = datetime.fromisoformat(test_date)
        except ValueError:
            test_date = datetime.now()

    test = SoilTest(
        test_date=test_date or datetime.now(),
        zone_id=data.get("zone_id"),
        lab_name=data.get("lab_name"),
        ph=data.get("ph"),
        buffer_ph=data.get("buffer_ph"),
        nitrogen_ppm=data.get("nitrogen_ppm"),
        phosphorus_ppm=data.get("phosphorus_ppm"),
        potassium_ppm=data.get("potassium_ppm"),
        calcium_ppm=data.get("calcium_ppm"),
        magnesium_ppm=data.get("magnesium_ppm"),
        sulfur_ppm=data.get("sulfur_ppm"),
        organic_matter_pct=data.get("organic_matter_pct"),
        cec=data.get("cec"),
        lime_recommendation_lbs_per_1k=data.get("lime_recommendation_lbs_per_1k"),
        notes=data.get("notes"),
        raw_data=data.get("raw_data"),
    )
    db.add(test)
    await db.flush()
    return _soil_test_dict(test)


@router.get("/latest")
async def latest_soil_test(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SoilTest).order_by(desc(SoilTest.test_date)).limit(1))
    t = result.scalar_one_or_none()
    if not t:
        return None

    # Include interpretation
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()

    zones_r = await db.execute(select(LawnZone))
    zones = zones_r.scalars().all()
    total_sqft = sum(z.area_sqft or 0 for z in zones) or 5000

    test_dict = _soil_test_dict(t)
    test_dict["interpretation"] = interpret_soil_test(
        {k: test_dict[k] for k in ["ph", "phosphorus_ppm", "potassium_ppm", "calcium_ppm",
                                     "magnesium_ppm", "organic_matter_pct", "buffer_ph"] if test_dict.get(k)},
        area_sqft=total_sqft,
    )
    return test_dict


@router.get("/{test_id}")
async def get_soil_test(test_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SoilTest).where(SoilTest.id == test_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Soil test not found")

    zone_name = None
    if t.zone_id:
        zr = await db.execute(select(LawnZone.name).where(LawnZone.id == t.zone_id))
        zone_name = zr.scalar_one_or_none()

    d = _soil_test_dict(t, zone_name)

    zones_r = await db.execute(select(LawnZone))
    zones = zones_r.scalars().all()
    total_sqft = sum(z.area_sqft or 0 for z in zones) or 5000

    d["interpretation"] = interpret_soil_test(
        {k: d[k] for k in ["ph", "phosphorus_ppm", "potassium_ppm", "calcium_ppm",
                             "magnesium_ppm", "organic_matter_pct", "buffer_ph"] if d.get(k)},
        area_sqft=total_sqft,
    )
    return d


@router.put("/{test_id}")
async def update_soil_test(test_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SoilTest).where(SoilTest.id == test_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Soil test not found")

    for key in ["lab_name", "ph", "buffer_ph", "nitrogen_ppm", "phosphorus_ppm", "potassium_ppm",
                "calcium_ppm", "magnesium_ppm", "sulfur_ppm", "organic_matter_pct", "cec",
                "lime_recommendation_lbs_per_1k", "notes", "zone_id"]:
        if key in data:
            setattr(t, key, data[key])

    if "test_date" in data:
        try:
            t.test_date = datetime.fromisoformat(data["test_date"])
        except (ValueError, TypeError):
            pass

    return _soil_test_dict(t)


@router.delete("/{test_id}")
async def delete_soil_test(test_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SoilTest).where(SoilTest.id == test_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Soil test not found")
    await db.delete(t)
    return {"ok": True}


@router.post("/calculate-amendment")
async def calculate_amendment(data: dict, db: AsyncSession = Depends(get_db)):
    """Calculate lime or sulfur needed to correct soil pH."""
    current_ph = data.get("current_ph")
    if not current_ph:
        raise HTTPException(400, "current_ph is required")

    target_ph = data.get("target_ph", 6.5)
    area_sqft = data.get("area_sqft", 5000)
    soil_type = data.get("soil_type", "loam")
    buffer_ph = data.get("buffer_ph")

    result = {}
    if current_ph < target_ph:
        result["lime"] = calculate_lime_needed(current_ph, target_ph, area_sqft, soil_type, buffer_ph)
    elif current_ph > target_ph:
        result["sulfur"] = calculate_sulfur_needed(current_ph, target_ph, area_sqft, soil_type)
    else:
        result["message"] = "pH is already at target. No amendment needed."

    result["current_ph"] = current_ph
    result["target_ph"] = target_ph
    result["area_sqft"] = area_sqft
    return result
