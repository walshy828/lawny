"""Schedule API — maintenance schedules and upcoming tasks."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from app.database import get_db
from app.models import MaintenanceSchedule, LawnZone
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate

router = APIRouter(prefix="/api", tags=["schedule"])


@router.get("/schedules")
async def list_schedules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MaintenanceSchedule).order_by(MaintenanceSchedule.next_due))
    schedules = result.scalars().all()
    now = datetime.now()

    items = []
    for s in schedules:
        zone_name = None
        if s.zone_id:
            zr = await db.execute(select(LawnZone.name).where(LawnZone.id == s.zone_id))
            zone_name = zr.scalar_one_or_none()

        days_until = None
        is_overdue = False
        if s.next_due:
            nd = s.next_due.replace(tzinfo=None) if s.next_due.tzinfo else s.next_due
            days_until = (nd - now).days
            is_overdue = days_until < 0

        items.append({
            **{c.name: getattr(s, c.name) for c in s.__table__.columns},
            "zone_name": zone_name,
            "days_until_due": days_until,
            "is_overdue": is_overdue,
        })

    return items


@router.post("/schedules")
async def create_schedule(data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    schedule = MaintenanceSchedule(**data.model_dump())
    if not schedule.next_due:
        schedule.next_due = datetime.now()
    db.add(schedule)
    await db.flush()
    return {c.name: getattr(schedule, c.name) for c in schedule.__table__.columns}


@router.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: int, data: ScheduleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MaintenanceSchedule).where(MaintenanceSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(404, "Schedule not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(schedule, key, value)

    return {c.name: getattr(schedule, c.name) for c in schedule.__table__.columns}


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MaintenanceSchedule).where(MaintenanceSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    await db.delete(schedule)
    return {"ok": True}


@router.post("/schedules/{schedule_id}/complete")
async def complete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a schedule as completed and advance the next_due date."""
    result = await db.execute(select(MaintenanceSchedule).where(MaintenanceSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(404, "Schedule not found")

    now = datetime.now()
    schedule.last_completed = now
    # Advance from the scheduled due date (not completion time) to preserve cadence.
    # If multiple periods are overdue, skip ahead until next_due is in the future.
    base = schedule.next_due.replace(tzinfo=None) if schedule.next_due and schedule.next_due.tzinfo else (schedule.next_due or now)
    next_due = base + timedelta(days=schedule.frequency_days)
    while next_due <= now:
        next_due += timedelta(days=schedule.frequency_days)
    schedule.next_due = next_due

    return {c.name: getattr(schedule, c.name) for c in schedule.__table__.columns}


@router.get("/schedules/upcoming")
async def upcoming_tasks(days: int = 14, db: AsyncSession = Depends(get_db)):
    """Get tasks due in the next N days (including overdue)."""
    cutoff = datetime.now() + timedelta(days=days)
    result = await db.execute(
        select(MaintenanceSchedule)
        .where(MaintenanceSchedule.is_active == True, MaintenanceSchedule.next_due <= cutoff)
        .order_by(MaintenanceSchedule.next_due)
    )
    schedules = result.scalars().all()
    now = datetime.now()

    items = []
    for s in schedules:
        zone_name = None
        if s.zone_id:
            zr = await db.execute(select(LawnZone.name).where(LawnZone.id == s.zone_id))
            zone_name = zr.scalar_one_or_none()

        nd = s.next_due.replace(tzinfo=None) if s.next_due.tzinfo else s.next_due
        items.append({
            "id": s.id, "type": s.activity_type,
            "next_due": s.next_due.isoformat(),
            "days_until": (nd - now).days,
            "is_overdue": (nd - now).days < 0,
            "zone_name": zone_name,
            "frequency_days": s.frequency_days,
        })

    return items
