"""Dashboard aggregation service."""

import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models import LawnConfig, LawnZone, Activity, MaintenanceSchedule, WateringRecommendation

logger = logging.getLogger(__name__)


async def get_dashboard_data(db: AsyncSession) -> dict:
    """Aggregate all dashboard data into a single response."""

    # Get lawn config
    result = await db.execute(select(LawnConfig).limit(1))
    lawn = result.scalar_one_or_none()

    lawn_data = None
    if lawn:
        zones_result = await db.execute(select(LawnZone).where(LawnZone.lawn_id == lawn.id))
        zones = zones_result.scalars().all()
        total_sqft = sum(z.area_sqft or 0 for z in zones)
        lawn_data = {
            "id": lawn.id, "name": lawn.name, "grass_type": lawn.grass_type,
            "latitude": lawn.latitude, "longitude": lawn.longitude,
            "zone_count": len(zones), "total_sqft": round(total_sqft, 0),
            "has_location": bool(lawn.latitude and lawn.longitude),
        }

    # Recent activities (last 5)
    activities_result = await db.execute(
        select(Activity).order_by(desc(Activity.date)).limit(5)
    )
    recent_activities = []
    for a in activities_result.scalars().all():
        zone_name = None
        if a.zone_id:
            zr = await db.execute(select(LawnZone.name).where(LawnZone.id == a.zone_id))
            zone_name = zr.scalar_one_or_none()
        recent_activities.append({
            "id": a.id, "type": a.activity_type, "date": a.date.isoformat() if a.date else None,
            "zone_name": zone_name, "health_score": a.health_score, "notes": a.notes,
        })

    # Health trend (last 20 scores)
    health_result = await db.execute(
        select(Activity.date, Activity.health_score)
        .where(Activity.health_score.isnot(None))
        .order_by(desc(Activity.date)).limit(20)
    )
    health_trend = [{"date": r[0].isoformat() if r[0] else None, "score": r[1]} for r in health_result.all()]
    health_trend.reverse()

    # Average health score
    avg_result = await db.execute(
        select(func.avg(Activity.health_score)).where(Activity.health_score.isnot(None))
    )
    avg_health = avg_result.scalar_one_or_none()

    # Last mow
    mow_result = await db.execute(
        select(Activity.date).where(Activity.activity_type == "mow").order_by(desc(Activity.date)).limit(1)
    )
    last_mow = mow_result.scalar_one_or_none()
    days_since_mow = (datetime.now(last_mow.tzinfo) - last_mow).days if last_mow else None

    # Upcoming schedules (next 14 days)
    upcoming = []
    sched_result = await db.execute(
        select(MaintenanceSchedule).where(MaintenanceSchedule.is_active == True).order_by(MaintenanceSchedule.next_due)
    )
    now = datetime.now()
    for s in sched_result.scalars().all():
        if s.next_due:
            days_until = (s.next_due.replace(tzinfo=None) - now).days if s.next_due.tzinfo else (s.next_due - now).days
            zone_name = None
            if s.zone_id:
                zr = await db.execute(select(LawnZone.name).where(LawnZone.id == s.zone_id))
                zone_name = zr.scalar_one_or_none()
            upcoming.append({
                "id": s.id, "type": s.activity_type, "next_due": s.next_due.isoformat(),
                "days_until": days_until, "is_overdue": days_until < 0,
                "zone_name": zone_name,
            })

    # Latest watering recommendation
    water_result = await db.execute(
        select(WateringRecommendation).order_by(desc(WateringRecommendation.date)).limit(1)
    )
    water_rec = water_result.scalar_one_or_none()
    watering_data = None
    if water_rec:
        watering_data = {
            "recommendation": water_rec.recommendation, "frequency": water_rec.frequency,
            "duration_minutes": water_rec.duration_minutes, "reasoning": water_rec.reasoning,
            "date": water_rec.date.isoformat() if water_rec.date else None,
        }

    return {
        "lawn": lawn_data,
        "recent_activities": recent_activities,
        "health_trend": health_trend,
        "avg_health_score": round(avg_health, 1) if avg_health else None,
        "last_mow": last_mow.isoformat() if last_mow else None,
        "days_since_mow": days_since_mow,
        "upcoming_tasks": upcoming[:7],
        "watering": watering_data,
    }
