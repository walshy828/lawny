"""Fertilizer Programs API — browse, activate, track adherence."""

import math
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc, func
from typing import Optional
from app.database import get_db
from app.models import LawnConfig, LawnZone
from app.models.fertilizer import FertilizerProgram, FertilizerStep, FertilizerApplication
from app.schemas.fertilizer import (
    CustomProgramCreate, CustomProgramUpdate, CustomStepCreate, CustomStepUpdate, ApplyStepRequest,
)
from app.services.fertilizer_catalog import seed_builtin_programs, MONTH_NAMES, SEASON_LABELS

router = APIRouter(prefix="/api/fertilizer", tags=["fertilizer"])


# ── Browse Programs ─────────────────────────────────────────────

@router.get("/programs")
async def list_programs(db: AsyncSession = Depends(get_db)):
    """List all programs, with climate-aware recommended sort."""
    # Get user's grass type for recommendations
    lawn_result = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_result.scalar_one_or_none()
    grass_type = lawn.grass_type if lawn else None

    # Determine grass season
    from app.services.recommendations import GRASS_PROFILES
    profile = GRASS_PROFILES.get(grass_type, {})
    user_season = profile.get("season", None)

    result = await db.execute(
        select(FertilizerProgram).order_by(FertilizerProgram.brand, FertilizerProgram.name)
    )
    programs = result.scalars().all()

    items = []
    for p in programs:
        # Load steps count
        steps_r = await db.execute(
            select(func.count()).select_from(FertilizerStep).where(FertilizerStep.program_id == p.id)
        )
        step_count = steps_r.scalar_one_or_none() or 0

        # Calculate recommendation score
        recommended = False
        if user_season:
            if p.grass_season == user_season or p.grass_season == "any" or p.grass_season == "transition":
                recommended = True

        items.append({
            "id": p.id, "name": p.name, "slug": p.slug, "brand": p.brand,
            "description": p.description, "grass_season": p.grass_season,
            "soil_type": p.soil_type, "is_builtin": p.is_builtin,
            "is_custom": p.is_custom, "step_count": step_count,
            "year": p.year, "recommended": recommended,
        })

    # Sort: recommended first, then by brand
    items.sort(key=lambda x: (not x["recommended"], x.get("brand") or "zzz", x["name"]))
    return items


@router.get("/programs/{program_id}")
async def get_program(program_id: int, db: AsyncSession = Depends(get_db)):
    """Get full program detail with all steps."""
    result = await db.execute(
        select(FertilizerProgram).where(FertilizerProgram.id == program_id)
    )
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Program not found")

    steps_r = await db.execute(
        select(FertilizerStep)
        .where(FertilizerStep.program_id == program.id)
        .order_by(FertilizerStep.step_number)
    )
    steps = steps_r.scalars().all()

    return {
        **{c.name: getattr(program, c.name) for c in program.__table__.columns},
        "steps": [{
            **{c.name: getattr(s, c.name) for c in s.__table__.columns},
            "season_label": SEASON_LABELS.get(s.season, s.season or ""),
            "month_label": f"{MONTH_NAMES.get(s.month_start, '')} – {MONTH_NAMES.get(s.month_end, '')}",
        } for s in steps],
    }


@router.post("/programs/refresh")
async def refresh_programs(db: AsyncSession = Depends(get_db)):
    """Re-seed built-in programs from the bundled catalog."""
    count = await seed_builtin_programs(db)
    return {"refreshed": count, "message": f"Refreshed {count} built-in programs from catalog"}


@router.post("/programs/ai-refresh")
async def ai_refresh_programs(db: AsyncSession = Depends(get_db)):
    """Use AI to generate updated fertilizer recommendations for the current year."""
    from app.services.ai_provider import get_provider
    import json

    year = datetime.now().year

    # Load lawn context
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    grass_type = lawn.grass_type if lawn else "unknown"

    try:
        from app.services.ai_provider import db_config_from_lawn
        provider_name = lawn.ai_provider if lawn and lawn.ai_provider else "openai"
        provider = get_provider(provider_name, db_config=db_config_from_lawn(lawn) if lawn else None)
    except Exception as e:
        raise HTTPException(503, f"AI provider not configured: {e}")

    lat = lawn.latitude if lawn else None
    lon = lawn.longitude if lawn else None
    location_hint = f"lat {lat:.1f}, lon {lon:.1f}" if lat and lon else "United States"

    prompt = f"""You are a professional lawn care agronomist. Generate a current {year} fertilizer program for:
- Grass type: {grass_type}
- Location: {location_hint}

Return a JSON object with:
{{
  "name": "program name",
  "description": "one-sentence description",
  "grass_season": "warm" | "cool" | "transition",
  "steps": [
    {{
      "step_number": 1,
      "product_name": "product name",
      "season": "spring" | "summer" | "fall" | "winter",
      "month_start": 3,
      "month_end": 4,
      "application_rate_per_1k": "rate string",
      "purpose": "purpose description",
      "tips": "application tips",
      "icon_emoji": "🌿"
    }}
  ]
}}
Focus on products widely available in {year}. Typical program has 4-6 steps."""

    try:
        raw = await provider.consult(prompt)
        # Extract JSON from response
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON in AI response")
        data = json.loads(raw[start:end])
    except Exception as e:
        raise HTTPException(422, f"AI returned invalid response: {e}")

    # Create a new custom program for this year
    slug = f"ai-{grass_type}-{year}".lower().replace(" ", "-")[:80]
    # Remove existing AI program for this year if present
    await db.execute(
        delete(FertilizerProgram).where(FertilizerProgram.slug == slug)
    )

    program = FertilizerProgram(
        name=data.get("name", f"AI Program {year}"),
        slug=slug,
        brand="AI Generated",
        description=data.get("description", ""),
        grass_season=data.get("grass_season", "any"),
        is_builtin=False,
        is_custom=True,
        year=year,
    )
    db.add(program)
    await db.flush()

    for i, s in enumerate(data.get("steps", []), 1):
        step = FertilizerStep(
            program_id=program.id,
            step_number=s.get("step_number", i),
            product_name=s.get("product_name", f"Step {i}"),
            season=s.get("season", "spring"),
            month_start=s.get("month_start"),
            month_end=s.get("month_end"),
            application_rate_per_1k=s.get("application_rate_per_1k"),
            purpose=s.get("purpose"),
            tips=s.get("tips"),
            icon_emoji=s.get("icon_emoji", "🌿"),
        )
        db.add(step)

    await db.commit()
    return {
        "message": f"AI-generated {year} program created: {program.name}",
        "program_id": program.id,
        "steps": len(data.get("steps", [])),
    }


# ── Custom Program CRUD ─────────────────────────────────────────

@router.post("/programs/custom")
async def create_custom_program(data: CustomProgramCreate, db: AsyncSession = Depends(get_db)):
    """Create a custom fertilizer program."""
    slug = data.name.lower().replace(" ", "-").replace("'", "")[:80]
    # Ensure unique slug
    existing = await db.execute(select(FertilizerProgram).where(FertilizerProgram.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{int(datetime.now().timestamp()) % 10000}"

    program = FertilizerProgram(
        name=data.name, slug=slug, description=data.description,
        grass_season=data.grass_season, soil_type=data.soil_type,
        is_builtin=False, is_custom=True, year=datetime.now().year,
    )
    db.add(program)
    await db.flush()
    return {c.name: getattr(program, c.name) for c in program.__table__.columns}


@router.put("/programs/custom/{program_id}")
async def update_custom_program(program_id: int, data: CustomProgramUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FertilizerProgram).where(
        FertilizerProgram.id == program_id, FertilizerProgram.is_custom == True
    ))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Custom program not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(program, k, v)
    return {c.name: getattr(program, c.name) for c in program.__table__.columns}


@router.delete("/programs/custom/{program_id}")
async def delete_custom_program(program_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FertilizerProgram).where(
        FertilizerProgram.id == program_id, FertilizerProgram.is_custom == True
    ))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Custom program not found")
    await db.delete(program)
    return {"ok": True}


@router.post("/programs/custom/{program_id}/steps")
async def add_custom_step(program_id: int, data: CustomStepCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FertilizerProgram).where(
        FertilizerProgram.id == program_id, FertilizerProgram.is_custom == True
    ))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Custom program not found")

    step = FertilizerStep(program_id=program.id, **data.model_dump())
    db.add(step)
    await db.flush()

    # Update step count
    count_r = await db.execute(select(func.count()).select_from(FertilizerStep).where(FertilizerStep.program_id == program.id))
    program.step_count = count_r.scalar_one_or_none() or 0

    return {c.name: getattr(step, c.name) for c in step.__table__.columns}


@router.put("/programs/custom/{program_id}/steps/{step_id}")
async def update_custom_step(program_id: int, step_id: int, data: CustomStepUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FertilizerStep).where(
        FertilizerStep.id == step_id, FertilizerStep.program_id == program_id
    ))
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Step not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(step, k, v)
    return {c.name: getattr(step, c.name) for c in step.__table__.columns}


@router.delete("/programs/custom/{program_id}/steps/{step_id}")
async def delete_custom_step(program_id: int, step_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FertilizerStep).where(
        FertilizerStep.id == step_id, FertilizerStep.program_id == program_id
    ))
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Step not found")
    await db.delete(step)

    # Update step count
    count_r = await db.execute(select(func.count()).select_from(FertilizerStep).where(FertilizerStep.program_id == program_id))
    prog_r = await db.execute(select(FertilizerProgram).where(FertilizerProgram.id == program_id))
    prog = prog_r.scalar_one_or_none()
    if prog:
        prog.step_count = count_r.scalar_one_or_none() or 0

    return {"ok": True}


# ── Active Program & Adherence ──────────────────────────────────

@router.get("/active")
async def get_active_program(db: AsyncSession = Depends(get_db)):
    """Get the user's active fertilizer program with adherence status."""
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    if not lawn or not lawn.active_program_id:
        return None

    prog_r = await db.execute(select(FertilizerProgram).where(FertilizerProgram.id == lawn.active_program_id))
    program = prog_r.scalar_one_or_none()
    if not program:
        return None

    # Get steps with application status
    steps_r = await db.execute(
        select(FertilizerStep).where(FertilizerStep.program_id == program.id).order_by(FertilizerStep.step_number)
    )
    steps = steps_r.scalars().all()

    current_year = datetime.now().year
    current_month = datetime.now().month

    step_details = []
    completed = 0
    for s in steps:
        # Get application record for this year
        app_r = await db.execute(
            select(FertilizerApplication).where(
                FertilizerApplication.step_id == s.id,
                FertilizerApplication.lawn_id == lawn.id,
                FertilizerApplication.year == current_year,
            )
        )
        app = app_r.scalar_one_or_none()

        status = "upcoming"
        if app:
            status = app.status
        elif s.month_start and s.month_end:
            if current_month >= s.month_start and current_month <= s.month_end:
                status = "current"
            elif current_month > s.month_end:
                status = "overdue"

        if status == "done":
            completed += 1

        step_details.append({
            **{c.name: getattr(s, c.name) for c in s.__table__.columns},
            "season_label": SEASON_LABELS.get(s.season, s.season or ""),
            "month_label": f"{MONTH_NAMES.get(s.month_start, '')} – {MONTH_NAMES.get(s.month_end, '')}",
            "status": status,
            "applied_date": app.applied_date.isoformat() if app and app.applied_date else None,
            "application_id": app.id if app else None,
            "notes": app.notes if app else None,
            "product_used": app.product_used if app else None,
        })

    total = len(steps)
    progress_pct = round((completed / total * 100) if total > 0 else 0)

    return {
        "program": {c.name: getattr(program, c.name) for c in program.__table__.columns},
        "steps": step_details,
        "completed": completed,
        "total": total,
        "progress_pct": progress_pct,
        "year": current_year,
    }


@router.post("/active")
async def activate_program(data: dict, db: AsyncSession = Depends(get_db)):
    """Activate a fertilizer program — creates application tracking rows for the year."""
    program_id = data.get("program_id")
    if not program_id:
        raise HTTPException(400, "program_id is required")

    prog_r = await db.execute(select(FertilizerProgram).where(FertilizerProgram.id == program_id))
    program = prog_r.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Program not found")

    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    if not lawn:
        raise HTTPException(404, "Lawn not configured")

    # Set as active program
    lawn.active_program_id = program_id

    # Create application rows for current year (if not already exists)
    current_year = datetime.now().year
    steps_r = await db.execute(
        select(FertilizerStep).where(FertilizerStep.program_id == program.id).order_by(FertilizerStep.step_number)
    )
    for step in steps_r.scalars().all():
        existing = await db.execute(
            select(FertilizerApplication).where(
                FertilizerApplication.step_id == step.id,
                FertilizerApplication.lawn_id == lawn.id,
                FertilizerApplication.year == current_year,
            )
        )
        if not existing.scalar_one_or_none():
            app = FertilizerApplication(
                step_id=step.id, lawn_id=lawn.id, year=current_year, status="pending",
            )
            db.add(app)

    return {"ok": True, "program_name": program.name}


@router.delete("/active")
async def deactivate_program(db: AsyncSession = Depends(get_db)):
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    if lawn:
        lawn.active_program_id = None
    return {"ok": True}


@router.post("/apply/{step_id}")
async def apply_step(step_id: int, data: ApplyStepRequest, db: AsyncSession = Depends(get_db)):
    """Mark a fertilizer step as applied or skipped."""
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    if not lawn:
        raise HTTPException(404, "Lawn not configured")

    current_year = datetime.now().year

    # Find or create application row
    app_r = await db.execute(
        select(FertilizerApplication).where(
            FertilizerApplication.step_id == step_id,
            FertilizerApplication.lawn_id == lawn.id,
            FertilizerApplication.year == current_year,
        )
    )
    app = app_r.scalar_one_or_none()
    if not app:
        app = FertilizerApplication(step_id=step_id, lawn_id=lawn.id, year=current_year)
        db.add(app)

    app.status = data.status
    app.applied_date = data.applied_date or (datetime.now() if data.status == "done" else None)
    app.notes = data.notes
    app.product_used = data.product_used

    return {"ok": True, "status": app.status}


# ── Shopping List ───────────────────────────────────────────────

@router.get("/shopping-list")
async def shopping_list(db: AsyncSession = Depends(get_db)):
    """Calculate bags needed for remaining steps based on lawn sqft."""
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    if not lawn or not lawn.active_program_id:
        return {"items": [], "total_sqft": 0}

    # Get total sqft
    zones_r = await db.execute(select(LawnZone).where(LawnZone.lawn_id == lawn.id))
    zones = zones_r.scalars().all()
    total_sqft = sum(z.area_sqft or 0 for z in zones)

    # Get steps not yet completed
    current_year = datetime.now().year
    steps_r = await db.execute(
        select(FertilizerStep)
        .where(FertilizerStep.program_id == lawn.active_program_id)
        .order_by(FertilizerStep.step_number)
    )
    steps = steps_r.scalars().all()

    items = []
    for s in steps:
        app_r = await db.execute(
            select(FertilizerApplication).where(
                FertilizerApplication.step_id == s.id,
                FertilizerApplication.lawn_id == lawn.id,
                FertilizerApplication.year == current_year,
            )
        )
        app = app_r.scalar_one_or_none()
        if app and app.status == "done":
            continue  # Skip completed steps

        bags_needed = 0
        if s.coverage_sqft_per_bag and s.coverage_sqft_per_bag > 0 and total_sqft > 0:
            bags_needed = math.ceil(total_sqft / s.coverage_sqft_per_bag)

        items.append({
            "step_number": s.step_number,
            "product_name": s.product_name,
            "season_label": SEASON_LABELS.get(s.season, s.season or ""),
            "month_label": f"{MONTH_NAMES.get(s.month_start, '')} – {MONTH_NAMES.get(s.month_end, '')}",
            "bags_needed": bags_needed,
            "coverage_per_bag": s.coverage_sqft_per_bag,
            "bag_weight": s.bag_weight,
            "total_sqft": total_sqft,
        })

    return {"items": items, "total_sqft": round(total_sqft)}
