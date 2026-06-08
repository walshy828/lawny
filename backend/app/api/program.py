"""Unified Lawn Program API — combines fertilizer schedule + AI remediation steps."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.lawn_program import LawnProgram, LawnProgramStep
from app.models.fertilizer import FertilizerStep, FertilizerApplication

router = APIRouter(prefix="/api/program", tags=["program"])

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

ACTIVITY_ICONS = {
    "fertilize": "🌿",
    "weed_control": "🌾",
    "pre_emergent": "🛡️",
    "post_emergent": "☠️",
    "fungicide": "🍄",
    "pest_control": "🪲",
    "overseed": "🌱",
    "aerate": "🔵",
    "lime": "🪨",
    "dethatch": "🧹",
    "mow": "✂️",
    "water": "💧",
    "other": "📋",
}


def _step_dict(s: LawnProgramStep) -> dict:
    return {
        "id": s.id,
        "program_id": s.program_id,
        "month": s.month,
        "month_name": MONTH_NAMES[s.month - 1] if s.month and 1 <= s.month <= 12 else None,
        "week_of_month": s.week_of_month,
        "activity_type": s.activity_type,
        "activity_icon": ACTIVITY_ICONS.get(s.activity_type or "", "📋"),
        "product_name": s.product_name,
        "application_rate": s.application_rate,
        "notes": s.notes,
        "priority": s.priority,
        "status": s.status,
        "source": s.source,
        "source_ref_id": s.source_ref_id,
        "conflicts_with": s.conflicts_with or [],
        "order_index": s.order_index,
        "completed_date": s.completed_date.isoformat() if s.completed_date else None,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _program_dict(p: LawnProgram, steps: list) -> dict:
    # Group steps by month
    by_month: dict[int, list] = {}
    for s in steps:
        m = s["month"] or 0
        by_month.setdefault(m, []).append(s)

    months = []
    for m in sorted(by_month.keys()):
        if m == 0:
            continue
        month_steps = sorted(by_month[m], key=lambda x: (x["order_index"], x["id"]))
        months.append({
            "month": m,
            "month_name": MONTH_NAMES[m - 1],
            "steps": month_steps,
        })

    pending = sum(1 for s in steps if s["status"] == "pending")
    done = sum(1 for s in steps if s["status"] == "done")
    total = len(steps)

    return {
        "id": p.id,
        "name": p.name,
        "season_year": p.season_year,
        "status": p.status,
        "description": p.description,
        "total_steps": total,
        "completed_steps": done,
        "pending_steps": pending,
        "progress_pct": round(done / total * 100) if total else 0,
        "steps": sorted(steps, key=lambda x: (x["month"] or 99, x["order_index"])),
        "by_month": months,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("/active")
async def get_active_program(db: AsyncSession = Depends(get_db)):
    """Get the active lawn program with all steps."""
    prog_r = await db.execute(select(LawnProgram).where(LawnProgram.status == "active").order_by(desc(LawnProgram.created_at)).limit(1))
    program = prog_r.scalar_one_or_none()
    if not program:
        return None

    steps_r = await db.execute(select(LawnProgramStep).where(LawnProgramStep.program_id == program.id))
    steps = [_step_dict(s) for s in steps_r.scalars().all()]
    return _program_dict(program, steps)


@router.get("")
async def list_programs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnProgram).order_by(desc(LawnProgram.created_at)))
    programs = result.scalars().all()
    out = []
    for p in programs:
        steps_r = await db.execute(select(LawnProgramStep).where(LawnProgramStep.program_id == p.id))
        steps = [_step_dict(s) for s in steps_r.scalars().all()]
        out.append(_program_dict(p, steps))
    return out


@router.post("")
async def create_program(data: dict, db: AsyncSession = Depends(get_db)):
    program = LawnProgram(
        name=data["name"],
        season_year=data.get("season_year", datetime.now(timezone.utc).year),
        status=data.get("status", "active"),
        description=data.get("description"),
    )
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return _program_dict(program, [])


@router.put("/{program_id}")
async def update_program(program_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnProgram).where(LawnProgram.id == program_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Program not found")

    for field in ["name", "status", "description", "season_year"]:
        if field in data:
            setattr(p, field, data[field])

    await db.commit()
    steps_r = await db.execute(select(LawnProgramStep).where(LawnProgramStep.program_id == p.id))
    steps = [_step_dict(s) for s in steps_r.scalars().all()]
    return _program_dict(p, steps)


@router.delete("/{program_id}")
async def delete_program(program_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnProgram).where(LawnProgram.id == program_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Program not found")
    await db.delete(p)
    await db.commit()
    return {"deleted": True}


@router.post("/generate")
async def generate_program(data: dict = {}, db: AsyncSession = Depends(get_db)):
    """
    Generate a unified lawn program by merging the active fertilizer program
    and the most recent AI remediation plan into a single calendar.
    Archives the previous active program first.
    """
    from app.models.assessment import RemediationPlan

    year = data.get("year", datetime.now(timezone.utc).year)
    now_month = datetime.now(timezone.utc).month

    # Archive existing active programs
    existing_r = await db.execute(select(LawnProgram).where(LawnProgram.status == "active"))
    for ep in existing_r.scalars().all():
        ep.status = "archived"

    program = LawnProgram(
        name=data.get("name", f"Lawn Program {year}"),
        season_year=year,
        status="active",
        description=data.get("description", "Generated from fertilizer program and AI remediation plan"),
    )
    db.add(program)
    await db.flush()

    steps_added = 0

    # --- Pull steps from the active fertilizer program ---
    from app.models.lawn import LawnConfig
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()

    if lawn and lawn.active_program_id:
        fert_steps_r = await db.execute(
            select(FertilizerStep)
            .where(FertilizerStep.program_id == lawn.active_program_id)
            .order_by(FertilizerStep.step_number)
        )
        fert_steps = fert_steps_r.scalars().all()

        for fs in fert_steps:
            # Skip already applied steps this year
            applied_r = await db.execute(
                select(FertilizerApplication).where(
                    FertilizerApplication.step_id == fs.id,
                    FertilizerApplication.lawn_id == lawn.id,
                    FertilizerApplication.year == year,
                    FertilizerApplication.status == "done",
                ).limit(1)
            )
            if applied_r.scalar_one_or_none():
                continue

            step = LawnProgramStep(
                program_id=program.id,
                month=fs.month_start or now_month,
                activity_type="fertilize",
                product_name=fs.product_name,
                application_rate=fs.application_rate_per_1k,
                notes=fs.purpose,
                priority="high",
                source="fertilizer",
                source_ref_id=fs.id,
                order_index=fs.step_number * 10,
            )
            db.add(step)
            steps_added += 1

    # --- Pull steps from the most recent remediation plan ---
    plan_r = await db.execute(select(RemediationPlan).order_by(desc(RemediationPlan.created_at)).limit(1))
    plan = plan_r.scalar_one_or_none()

    if plan and plan.action_steps:
        WEEK_TARGET_MONTH_MAP = {
            "Immediately": now_month,
            "Week 1-2": now_month,
            "Week 3-4": now_month,
            "Month 2": (now_month % 12) + 1,
            "Month 3": ((now_month + 1) % 12) + 1,
            "Fall": 9,
            "Spring": 3,
        }
        for i, step_data in enumerate(plan.action_steps):
            week_target = step_data.get("week_target", "Month 2")
            month = WEEK_TARGET_MONTH_MAP.get(week_target, now_month)
            week = 1 if "Week 1" in week_target else (3 if "Week 3" in week_target else None)

            step = LawnProgramStep(
                program_id=program.id,
                month=month,
                week_of_month=week,
                activity_type=step_data.get("activity_type", "other"),
                product_name=step_data.get("product_name"),
                application_rate=step_data.get("application_rate"),
                notes=step_data.get("description"),
                priority=step_data.get("priority", "medium"),
                source="ai_remediation",
                source_ref_id=plan.id,
                conflicts_with=step_data.get("conflicts_with", []),
                order_index=step_data.get("order", i + 1) * 10 + 5,
            )
            db.add(step)
            steps_added += 1

    await db.commit()

    steps_r = await db.execute(select(LawnProgramStep).where(LawnProgramStep.program_id == program.id))
    steps = [_step_dict(s) for s in steps_r.scalars().all()]
    return _program_dict(program, steps)


@router.post("/{program_id}/steps")
async def add_step(program_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnProgram).where(LawnProgram.id == program_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Program not found")

    step = LawnProgramStep(
        program_id=program_id,
        month=data.get("month"),
        week_of_month=data.get("week_of_month"),
        activity_type=data.get("activity_type", "other"),
        product_name=data.get("product_name"),
        application_rate=data.get("application_rate"),
        notes=data.get("notes"),
        priority=data.get("priority", "medium"),
        source="manual",
        order_index=data.get("order_index", 50),
    )
    db.add(step)
    await db.commit()
    await db.refresh(step)
    return _step_dict(step)


@router.put("/{program_id}/steps/{step_id}")
async def update_step(program_id: int, step_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnProgramStep).where(
        LawnProgramStep.id == step_id, LawnProgramStep.program_id == program_id
    ))
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Step not found")

    for field in ["month", "week_of_month", "activity_type", "product_name",
                  "application_rate", "notes", "priority", "status", "order_index"]:
        if field in data:
            setattr(step, field, data[field])

    await db.commit()
    await db.refresh(step)
    return _step_dict(step)


@router.post("/{program_id}/steps/{step_id}/complete")
async def complete_step(program_id: int, step_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnProgramStep).where(
        LawnProgramStep.id == step_id, LawnProgramStep.program_id == program_id
    ))
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Step not found")

    step.status = "done"
    step.completed_date = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(step)
    return _step_dict(step)


@router.delete("/{program_id}/steps/{step_id}")
async def delete_step(program_id: int, step_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnProgramStep).where(
        LawnProgramStep.id == step_id, LawnProgramStep.program_id == program_id
    ))
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Step not found")
    await db.delete(step)
    await db.commit()
    return {"deleted": True}
