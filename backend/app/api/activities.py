"""Activities API — log, list, and track lawn care events."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Activity, LawnZone, ACTIVITY_TYPES
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityStatsOut

router = APIRouter(prefix="/api", tags=["activities"])


@router.get("/activities")
async def list_activities(
    activity_type: Optional[str] = None,
    zone_id: Optional[int] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(Activity).order_by(desc(Activity.date))
    if activity_type:
        q = q.where(Activity.activity_type == activity_type)
    if zone_id:
        q = q.where(Activity.zone_id == zone_id)
    q = q.limit(limit).offset(offset)

    result = await db.execute(q)
    activities = result.scalars().all()

    items = []
    for a in activities:
        zone_name = None
        if a.zone_id:
            zr = await db.execute(select(LawnZone.name).where(LawnZone.id == a.zone_id))
            zone_name = zr.scalar_one_or_none()
        items.append({
            **{c.name: getattr(a, c.name) for c in a.__table__.columns},
            "zone_name": zone_name,
        })

    return items


@router.post("/activities")
async def create_activity(data: ActivityCreate, db: AsyncSession = Depends(get_db)):
    if data.activity_type not in ACTIVITY_TYPES:
        raise HTTPException(400, f"Invalid activity type. Valid types: {ACTIVITY_TYPES}")

    activity = Activity(**data.model_dump())
    if not activity.date:
        activity.date = datetime.now()
    db.add(activity)
    await db.flush()
    return {c.name: getattr(activity, c.name) for c in activity.__table__.columns}


@router.put("/activities/{activity_id}")
async def update_activity(activity_id: int, data: ActivityUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(404, "Activity not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(activity, key, value)

    return {c.name: getattr(activity, c.name) for c in activity.__table__.columns}


@router.delete("/activities/{activity_id}")
async def delete_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(404, "Activity not found")
    await db.delete(activity)
    return {"ok": True}


@router.get("/activities/types")
async def activity_types():
    return ACTIVITY_TYPES


@router.get("/activities/stats")
async def activity_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.now()

    # Last mow
    mow_r = await db.execute(select(Activity.date).where(Activity.activity_type == "mow").order_by(desc(Activity.date)).limit(1))
    last_mow = mow_r.scalar_one_or_none()

    # Last fertilize
    fert_r = await db.execute(select(Activity.date).where(Activity.activity_type == "fertilize").order_by(desc(Activity.date)).limit(1))
    last_fert = fert_r.scalar_one_or_none()

    # Avg health
    avg_r = await db.execute(select(func.avg(Activity.health_score)).where(Activity.health_score.isnot(None)))
    avg_health = avg_r.scalar_one_or_none()

    # Health trend (last 30 entries)
    trend_r = await db.execute(
        select(Activity.date, Activity.health_score)
        .where(Activity.health_score.isnot(None))
        .order_by(desc(Activity.date)).limit(30)
    )
    trend = [{"date": r[0].isoformat() if r[0] else None, "score": r[1]} for r in trend_r.all()]
    trend.reverse()

    # Activity counts
    count_r = await db.execute(select(Activity.activity_type, func.count()).group_by(Activity.activity_type))
    counts = {r[0]: r[1] for r in count_r.all()}

    # Total
    total_r = await db.execute(select(func.count()).select_from(Activity))
    total = total_r.scalar_one_or_none() or 0

    return {
        "total_activities": total,
        "last_mow": last_mow.isoformat() if last_mow else None,
        "days_since_mow": (now - last_mow.replace(tzinfo=None)).days if last_mow else None,
        "last_fertilize": last_fert.isoformat() if last_fert else None,
        "days_since_fertilize": (now - last_fert.replace(tzinfo=None)).days if last_fert else None,
        "avg_health_score": round(avg_health, 1) if avg_health else None,
        "health_trend": trend,
        "activity_counts": counts,
    }
