"""Timeline API — unified view across lawn program, fertilizer, schedules, and activity history."""

from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    Activity, LawnConfig, LawnZone, MaintenanceSchedule,
)
from app.models.fertilizer import FertilizerApplication, FertilizerStep
from app.models.lawn_program import LawnProgram, LawnProgramStep

router = APIRouter(prefix="/api/timeline", tags=["timeline"])

ACTIVITY_ICONS = {
    "fertilize": "🌿", "weed_control": "🌾", "pre_emergent": "🛡️",
    "post_emergent": "☠️", "fungicide": "🍄", "pest_control": "🪲",
    "overseed": "🌱", "aerate": "🔵", "lime": "🪨", "dethatch": "🧹",
    "mow": "✂️", "water": "💧", "soil_test": "🧫", "topdress": "🏔️",
    "edge": "✂️", "leaf_cleanup": "🍂", "other": "📋",
}

ACTIVITY_LABELS = {
    "fertilize": "Fertilize", "weed_control": "Weed Control",
    "pre_emergent": "Pre-Emergent", "post_emergent": "Post-Emergent",
    "fungicide": "Fungicide", "pest_control": "Pest Control",
    "overseed": "Overseed", "aerate": "Aerate", "lime": "Lime",
    "dethatch": "Dethatch", "mow": "Mow", "water": "Water",
    "soil_test": "Soil Test", "topdress": "Topdress", "edge": "Edge",
    "leaf_cleanup": "Leaf Cleanup", "other": "Other",
}


def _label(activity_type: Optional[str]) -> str:
    return ACTIVITY_LABELS.get(activity_type or "other", activity_type or "Other")


def _week_date(year: int, month: int, week_of_month: int) -> date:
    day = 1 + (week_of_month - 1) * 7
    last_day = monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def _month_date(year: int, month: int) -> date:
    return date(year, month, 15)


def _to_date(val) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        return date.fromisoformat(str(val)[:10])
    except Exception:
        return None


def _status(month: int, raw_status: str, today: date) -> str:
    if raw_status == "done":
        return "done"
    if raw_status == "skipped":
        return "skipped"
    # Treat the whole target month as the window — past the last day = overdue
    last_day_of_month = monthrange(today.year, month)[1]
    window_end = date(today.year, month, last_day_of_month)
    if today > window_end:
        return "overdue"
    if today.month == month:
        return "due"
    return "upcoming"


@router.get("")
async def get_timeline(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    include_history: bool = Query(True),
    history_days: int = Query(90),
    db: AsyncSession = Depends(get_db),
):
    """
    Unified timeline: lawn program steps + fertilizer applications +
    recurring schedules + activity history, sorted by status then date.
    """
    today = date.today()
    year = today.year
    items = []

    # ── 1. Active Lawn Program Steps ───────────────────────────────
    prog_r = await db.execute(
        select(LawnProgram)
        .where(LawnProgram.status == "active")
        .order_by(desc(LawnProgram.created_at))
        .limit(1)
    )
    program = prog_r.scalar_one_or_none()

    if program:
        steps_r = await db.execute(
            select(LawnProgramStep).where(LawnProgramStep.program_id == program.id)
        )
        for step in steps_r.scalars().all():
            if not step.month:
                continue
            if step.week_of_month:
                item_date = _week_date(year, step.month, step.week_of_month)
            else:
                item_date = _month_date(year, step.month)

            raw_status = step.status or "pending"
            status = _status(step.month, raw_status, today)
            completed_d = _to_date(step.completed_date)

            items.append({
                "id": f"lawn_step_{step.id}",
                "source": "lawn_program",
                "source_label": "Program",
                "title": _label(step.activity_type) + (f": {step.product_name}" if step.product_name else ""),
                "subtitle": step.notes,
                "activity_type": step.activity_type or "other",
                "icon": ACTIVITY_ICONS.get(step.activity_type or "", "📋"),
                "date": (completed_d.isoformat() if completed_d else item_date.isoformat()),
                "planned_date": item_date.isoformat(),
                "month": step.month,
                "week_of_month": step.week_of_month,
                "status": status,
                "priority": step.priority,
                "product_name": step.product_name,
                "zone_name": None,
                "ref_id": step.id,
                "ref_program_id": step.program_id,
                "ref_type": "LawnProgramStep",
                "can_complete": status not in ("done", "skipped"),
                "completed_date": completed_d.isoformat() if completed_d else None,
            })

    # ── 2. Fertilizer Applications (active program) ─────────────────
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()

    if lawn and lawn.active_program_id:
        rows = await db.execute(
            select(FertilizerApplication, FertilizerStep)
            .join(FertilizerStep, FertilizerApplication.step_id == FertilizerStep.id)
            .where(
                FertilizerApplication.lawn_id == lawn.id,
                FertilizerApplication.year == year,
            )
            .order_by(FertilizerStep.step_number)
        )
        for app, step in rows.all():
            # Skip if same step already appears as lawn program step (via source_ref_id)
            if program:
                already = any(
                    i["ref_type"] == "LawnProgramStep"
                    and i.get("ref_id") is not None
                    # soft-linked via source_ref_id in LawnProgramStep
                    for i in items
                )
                # Only deduplicate if this fert step is referenced in a lawn program step
                pass  # We'll show both — fertilizer view is the authoritative tracking

            if step.month_start:
                item_date = _month_date(year, step.month_start)
            else:
                item_date = today

            raw_status = app.status or "pending"
            status = _status(step.month_start or today.month, raw_status, today)
            applied_d = _to_date(app.applied_date)

            items.append({
                "id": f"fert_app_{app.id}",
                "source": "fertilizer",
                "source_label": "Fertilizer",
                "title": f"Step {step.step_number}: {step.product_name}",
                "subtitle": step.purpose,
                "activity_type": "fertilize",
                "icon": step.icon_emoji or "🌿",
                "date": (applied_d.isoformat() if applied_d else item_date.isoformat()),
                "planned_date": item_date.isoformat(),
                "month": step.month_start,
                "week_of_month": None,
                "status": status,
                "priority": "high",
                "product_name": step.product_name,
                "zone_name": None,
                "ref_id": app.id,
                "ref_step_id": step.id,
                "ref_type": "FertilizerApplication",
                "can_complete": status not in ("done", "skipped"),
                "completed_date": applied_d.isoformat() if applied_d else None,
            })

    # ── 3. Recurring Maintenance Schedules ──────────────────────────
    sched_r = await db.execute(
        select(MaintenanceSchedule).where(MaintenanceSchedule.is_active == True)
    )
    for sched in sched_r.scalars().all():
        zone_name = None
        if sched.zone_id:
            zr = await db.execute(select(LawnZone.name).where(LawnZone.id == sched.zone_id))
            zone_name = zr.scalar_one_or_none()

        nd_date = _to_date(sched.next_due) or today
        days_until = (nd_date - today).days
        if days_until < 0:
            status = "overdue"
        elif days_until <= 7:
            status = "due"
        else:
            status = "upcoming"

        last_comp_d = _to_date(sched.last_completed)
        subtitle_parts = [f"Every {sched.frequency_days} days"]
        if sched.notes:
            subtitle_parts.append(sched.notes)

        items.append({
            "id": f"schedule_{sched.id}",
            "source": "schedule",
            "source_label": "Schedule",
            "title": _label(sched.activity_type),
            "subtitle": " · ".join(subtitle_parts),
            "activity_type": sched.activity_type or "other",
            "icon": ACTIVITY_ICONS.get(sched.activity_type or "", "📋"),
            "date": nd_date.isoformat(),
            "planned_date": nd_date.isoformat(),
            "month": nd_date.month,
            "week_of_month": None,
            "status": status,
            "priority": None,
            "product_name": None,
            "zone_name": zone_name,
            "ref_id": sched.id,
            "ref_type": "MaintenanceSchedule",
            "can_complete": True,
            "completed_date": last_comp_d.isoformat() if last_comp_d else None,
        })

    # ── 4. Activity History ─────────────────────────────────────────
    if include_history:
        history_start = datetime.combine(today - timedelta(days=history_days), datetime.min.time())
        acts_r = await db.execute(
            select(Activity)
            .where(Activity.date >= history_start)
            .order_by(desc(Activity.date))
            .limit(200)
        )
        for act in acts_r.scalars().all():
            zone_name = None
            if act.zone_id:
                zr = await db.execute(select(LawnZone.name).where(LawnZone.id == act.zone_id))
                zone_name = zr.scalar_one_or_none()

            act_date = _to_date(act.date) or today
            products_used = act.products_used or []
            if isinstance(products_used, list):
                product_str = ", ".join(
                    p.get("name", "") if isinstance(p, dict) else str(p)
                    for p in products_used if p
                ) or None
            else:
                product_str = str(products_used) if products_used else None

            items.append({
                "id": f"activity_{act.id}",
                "source": "activity",
                "source_label": "History",
                "title": _label(act.activity_type),
                "subtitle": act.notes,
                "activity_type": act.activity_type or "other",
                "icon": ACTIVITY_ICONS.get(act.activity_type or "", "📋"),
                "date": act_date.isoformat(),
                "planned_date": act_date.isoformat(),
                "month": act_date.month,
                "week_of_month": None,
                "status": "done",
                "priority": None,
                "product_name": product_str,
                "zone_name": zone_name,
                "ref_id": act.id,
                "ref_type": "Activity",
                "can_complete": False,
                "completed_date": act_date.isoformat(),
            })

    # ── Filter by date range ────────────────────────────────────────
    if start:
        items = [i for i in items if i["date"] >= start]
    if end:
        items = [i for i in items if i["date"] <= end]

    # ── Sort: overdue → due → upcoming → done → skipped ─────────────
    order = {"overdue": 0, "due": 1, "upcoming": 2, "done": 3, "skipped": 4}
    items.sort(key=lambda x: (order.get(x["status"], 5), x["date"]))

    return {
        "items": items,
        "today": today.isoformat(),
        "summary": {
            "overdue": sum(1 for i in items if i["status"] == "overdue"),
            "due": sum(1 for i in items if i["status"] == "due"),
            "upcoming": sum(1 for i in items if i["status"] == "upcoming"),
            "done": sum(1 for i in items if i["status"] == "done"),
        },
    }
