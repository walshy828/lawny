"""Lawn Assessment API — multi-finding assessment sessions with AI remediation plans."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.assessment import LawnAssessment, AssessmentFinding, RemediationPlan
from app.models.lawn import LawnConfig, LawnZone
from app.models.soil_test import SoilTest
from app.models.weather import WeatherSnapshot
from app.services.ai_provider import get_provider, _parse_json_response, ASSESSMENT_SYSTEM_PROMPT, db_config_from_lawn
from app.services.seasonal_calendar import get_active_alerts, get_region_for_coords
from app.models.observation import OBSERVATION_TYPE_META

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


def _finding_dict(f: AssessmentFinding) -> dict:
    meta = OBSERVATION_TYPE_META.get(f.finding_type, {})
    return {
        "id": f.id,
        "assessment_id": f.assessment_id,
        "finding_type": f.finding_type,
        "type_label": meta.get("label", f.finding_type.replace("_", " ").title()),
        "type_icon": meta.get("icon", "🔍"),
        "severity": f.severity,
        "coverage_pct": f.coverage_pct,
        "location_notes": f.location_notes,
        "photo_url": f.photo_url,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


def _assessment_dict(a: LawnAssessment, findings: list, plan: Optional[RemediationPlan] = None, zone_name: Optional[str] = None) -> dict:
    return {
        "id": a.id,
        "zone_id": a.zone_id,
        "zone_name": zone_name,
        "date": a.date.isoformat() if a.date else None,
        "overall_condition": a.overall_condition,
        "grass_coverage_pct": a.grass_coverage_pct,
        "notes": a.notes,
        "ai_analyzed": a.ai_analyzed,
        "finding_count": len(findings),
        "findings": [_finding_dict(f) for f in findings],
        "remediation_plan": _plan_dict(plan) if plan else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _plan_dict(p: RemediationPlan) -> dict:
    return {
        "id": p.id,
        "assessment_id": p.assessment_id,
        "findings_summary": p.findings_summary,
        "action_steps": p.action_steps or [],
        "key_warnings": p.key_warnings or [],
        "expected_outcomes": p.expected_outcomes or [],
        "seasonal_context": p.seasonal_context,
        "ai_provider": p.ai_provider,
        "ai_model": p.ai_model,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


async def _get_lawn_context(db: AsyncSession) -> dict:
    """Build the full lawn context string for AI prompting."""
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    if not lawn:
        return {}

    zones_r = await db.execute(select(LawnZone))
    zones = zones_r.scalars().all()
    total_sqft = sum(z.area_sqft or 0 for z in zones) or 5000

    # Latest soil test
    soil_r = await db.execute(select(SoilTest).order_by(desc(SoilTest.test_date)).limit(1))
    soil = soil_r.scalar_one_or_none()

    # Latest weather snapshot (most recent daily record)
    weather_r = await db.execute(select(WeatherSnapshot).order_by(desc(WeatherSnapshot.date)).limit(1))
    weather = weather_r.scalar_one_or_none()

    # Seasonal alerts
    month = datetime.now(timezone.utc).month
    alerts = []
    if lawn.latitude and lawn.longitude:
        alerts = get_active_alerts(month=month, lat=lawn.latitude, lon=lawn.longitude, grass_type=lawn.grass_type)

    context = {
        "lawn": {
            "name": lawn.name,
            "grass_type": lawn.grass_type or "unknown",
            "total_sqft": total_sqft,
            "latitude": lawn.latitude,
            "longitude": lawn.longitude,
            "usda_zone": lawn.usda_zone,
        },
        "current_month": month,
        "current_month_name": datetime.now(timezone.utc).strftime("%B"),
        "current_year": datetime.now(timezone.utc).year,
        "soil": {
            "ph": soil.ph,
            "organic_matter_pct": soil.organic_matter_pct,
            "nitrogen_ppm": soil.nitrogen_ppm,
            "phosphorus_ppm": soil.phosphorus_ppm,
            "potassium_ppm": soil.potassium_ppm,
            "test_date": soil.test_date.strftime("%Y-%m") if soil and soil.test_date else None,
        } if soil else None,
        "weather": {
            "temp_high_f": weather.temp_high_f if weather else None,
            "soil_temp_f": weather.soil_temp_0cm_f if weather else None,
        } if weather else None,
        "active_seasonal_alerts": [a.get("title") for a in alerts[:5]] if alerts else [],
    }
    return context


def _format_assessment_prompt(assessment: LawnAssessment, findings: list[AssessmentFinding], lawn_ctx: dict) -> str:
    lines = []

    lawn = lawn_ctx.get("lawn", {})
    lines.append(f"LAWN: {lawn.get('name', 'Unknown')} | Grass: {lawn.get('grass_type', 'unknown')} | Size: {lawn.get('total_sqft', 0):,} sqft")
    lines.append(f"DATE: {lawn_ctx.get('current_month_name', '')} {lawn_ctx.get('current_year', '')}")

    if lawn.get("latitude"):
        lines.append(f"LOCATION: {lawn['latitude']:.2f}°N, {lawn['longitude']:.2f}°W")
    if lawn.get("usda_zone"):
        lines.append(f"USDA Zone: {lawn['usda_zone']}")

    soil = lawn_ctx.get("soil")
    if soil:
        parts = [f"pH {soil['ph']}" if soil.get("ph") else None,
                 f"N={soil['nitrogen_ppm']}ppm" if soil.get("nitrogen_ppm") else None,
                 f"P={soil['phosphorus_ppm']}ppm" if soil.get("phosphorus_ppm") else None,
                 f"K={soil['potassium_ppm']}ppm" if soil.get("potassium_ppm") else None,
                 f"OM={soil['organic_matter_pct']}%" if soil.get("organic_matter_pct") else None]
        lines.append(f"SOIL: {' | '.join(p for p in parts if p)} (tested {soil.get('test_date', 'unknown')})")

    weather = lawn_ctx.get("weather")
    if weather and weather.get("temp_high_f"):
        lines.append(f"CURRENT CONDITIONS: {weather['temp_high_f']:.0f}°F high temp" +
                     (f", {weather['soil_temp_f']:.0f}°F soil temp" if weather.get("soil_temp_f") else ""))

    alerts = lawn_ctx.get("active_seasonal_alerts", [])
    if alerts:
        lines.append(f"ACTIVE SEASONAL ALERTS: {', '.join(alerts)}")

    lines.append("")
    lines.append(f"ASSESSMENT DATE: {assessment.date.strftime('%Y-%m-%d') if assessment.date else 'today'}")
    lines.append(f"OVERALL CONDITION: {assessment.overall_condition or 'not specified'}")
    if assessment.grass_coverage_pct is not None:
        lines.append(f"GRASS COVERAGE: {assessment.grass_coverage_pct}% (rest is weeds, bare spots, or other)")
    if assessment.notes:
        lines.append(f"NOTES: {assessment.notes}")

    lines.append("")
    lines.append(f"FINDINGS ({len(findings)} issues identified):")
    for i, f in enumerate(findings, 1):
        meta = OBSERVATION_TYPE_META.get(f.finding_type, {})
        label = meta.get("label", f.finding_type.replace("_", " ").title())
        parts = [f"{i}. {label}"]
        if f.severity:
            parts.append(f"severity={f.severity}")
        if f.coverage_pct is not None:
            parts.append(f"coverage={f.coverage_pct}%")
        if f.location_notes:
            parts.append(f'location="{f.location_notes}"')
        lines.append("  " + " | ".join(parts))

    lines.append("")
    lines.append("Please create a comprehensive, conflict-aware remediation plan for ALL of these findings. "
                 "Order actions by urgency and treatment dependencies. Flag any conflicts between treatments.")

    return "\n".join(lines)


@router.get("")
async def list_assessments(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnAssessment).order_by(desc(LawnAssessment.date)).limit(limit))
    assessments = result.scalars().all()

    out = []
    for a in assessments:
        findings_r = await db.execute(select(AssessmentFinding).where(AssessmentFinding.assessment_id == a.id))
        findings = findings_r.scalars().all()

        zone_name = None
        if a.zone_id:
            zr = await db.execute(select(LawnZone.name).where(LawnZone.id == a.zone_id))
            zone_name = zr.scalar_one_or_none()

        out.append(_assessment_dict(a, findings, zone_name=zone_name))

    return out


@router.post("")
async def create_assessment(data: dict, db: AsyncSession = Depends(get_db)):
    """Create an assessment with optional inline findings."""
    a = LawnAssessment(
        zone_id=data.get("zone_id"),
        date=datetime.fromisoformat(data["date"]) if data.get("date") else datetime.now(timezone.utc),
        overall_condition=data.get("overall_condition"),
        grass_coverage_pct=data.get("grass_coverage_pct"),
        notes=data.get("notes"),
    )
    db.add(a)
    await db.flush()

    findings_data = data.get("findings", [])
    findings = []
    for fd in findings_data:
        f = AssessmentFinding(
            assessment_id=a.id,
            finding_type=fd["finding_type"],
            severity=fd.get("severity"),
            coverage_pct=fd.get("coverage_pct"),
            location_notes=fd.get("location_notes"),
        )
        db.add(f)
        findings.append(f)

    await db.commit()
    await db.refresh(a)
    for f in findings:
        await db.refresh(f)

    return _assessment_dict(a, findings)


@router.get("/{assessment_id}")
async def get_assessment(assessment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnAssessment).where(LawnAssessment.id == assessment_id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(404, "Assessment not found")

    findings_r = await db.execute(select(AssessmentFinding).where(AssessmentFinding.assessment_id == assessment_id))
    findings = findings_r.scalars().all()

    plan_r = await db.execute(select(RemediationPlan).where(RemediationPlan.assessment_id == assessment_id).order_by(desc(RemediationPlan.created_at)).limit(1))
    plan = plan_r.scalar_one_or_none()

    zone_name = None
    if a.zone_id:
        zr = await db.execute(select(LawnZone.name).where(LawnZone.id == a.zone_id))
        zone_name = zr.scalar_one_or_none()

    return _assessment_dict(a, list(findings), plan, zone_name=zone_name)


@router.put("/{assessment_id}")
async def update_assessment(assessment_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnAssessment).where(LawnAssessment.id == assessment_id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(404, "Assessment not found")

    for field in ["overall_condition", "grass_coverage_pct", "notes", "zone_id"]:
        if field in data:
            setattr(a, field, data[field])

    await db.commit()
    await db.refresh(a)

    findings_r = await db.execute(select(AssessmentFinding).where(AssessmentFinding.assessment_id == assessment_id))
    findings = findings_r.scalars().all()
    return _assessment_dict(a, list(findings))


@router.delete("/{assessment_id}")
async def delete_assessment(assessment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnAssessment).where(LawnAssessment.id == assessment_id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(404, "Assessment not found")
    await db.delete(a)
    await db.commit()
    return {"deleted": True}


@router.post("/{assessment_id}/findings")
async def add_finding(assessment_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnAssessment).where(LawnAssessment.id == assessment_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Assessment not found")

    f = AssessmentFinding(
        assessment_id=assessment_id,
        finding_type=data["finding_type"],
        severity=data.get("severity"),
        coverage_pct=data.get("coverage_pct"),
        location_notes=data.get("location_notes"),
    )
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return _finding_dict(f)


@router.put("/{assessment_id}/findings/{finding_id}")
async def update_finding(assessment_id: int, finding_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AssessmentFinding).where(
        AssessmentFinding.id == finding_id,
        AssessmentFinding.assessment_id == assessment_id,
    ))
    f = result.scalar_one_or_none()
    if not f:
        raise HTTPException(404, "Finding not found")

    for field in ["finding_type", "severity", "coverage_pct", "location_notes"]:
        if field in data:
            setattr(f, field, data[field])

    await db.commit()
    await db.refresh(f)
    return _finding_dict(f)


@router.delete("/{assessment_id}/findings/{finding_id}")
async def delete_finding(assessment_id: int, finding_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AssessmentFinding).where(
        AssessmentFinding.id == finding_id,
        AssessmentFinding.assessment_id == assessment_id,
    ))
    f = result.scalar_one_or_none()
    if not f:
        raise HTTPException(404, "Finding not found")
    await db.delete(f)
    await db.commit()
    return {"deleted": True}


@router.post("/{assessment_id}/analyze")
async def analyze_assessment(assessment_id: int, data: dict = {}, db: AsyncSession = Depends(get_db)):
    """Run AI analysis on the full assessment and save a RemediationPlan."""
    result = await db.execute(select(LawnAssessment).where(LawnAssessment.id == assessment_id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(404, "Assessment not found")

    findings_r = await db.execute(select(AssessmentFinding).where(AssessmentFinding.assessment_id == assessment_id))
    findings = list(findings_r.scalars().all())

    if not findings:
        raise HTTPException(400, "Add at least one finding before analyzing")

    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    lawn_ctx = await _get_lawn_context(db)
    prompt = _format_assessment_prompt(a, findings, lawn_ctx)

    provider_name = data.get("ai_provider") or (lawn.ai_provider if lawn else None)
    provider = get_provider(provider_name, db_config=db_config_from_lawn(lawn))

    raw = await provider.analyze_assessment(prompt)

    try:
        structured = _parse_json_response(raw)
    except Exception:
        structured = {"findings_summary": raw, "action_steps": [], "key_warnings": [], "expected_outcomes": []}

    # Delete old plan for this assessment if any
    old_r = await db.execute(select(RemediationPlan).where(RemediationPlan.assessment_id == assessment_id))
    for old in old_r.scalars().all():
        await db.delete(old)

    plan = RemediationPlan(
        assessment_id=assessment_id,
        findings_summary=structured.get("findings_summary"),
        action_steps=structured.get("action_steps", []),
        key_warnings=structured.get("key_warnings", []),
        expected_outcomes=structured.get("expected_outcomes", []),
        seasonal_context=structured.get("seasonal_context"),
        ai_provider=provider.provider_name,
        ai_model=provider.model_name,
        raw_response=raw,
    )
    db.add(plan)

    a.ai_analyzed = True
    await db.commit()
    await db.refresh(plan)

    return _plan_dict(plan)


def _resolve_step_month(step_data: dict, now_month: int) -> tuple[int, int | None]:
    """Return (month 1-12, week 1-4|None) for an action step using AI-provided fields."""
    # Prefer explicit schedule_month from AI
    sm = step_data.get("schedule_month")
    if isinstance(sm, int) and 1 <= sm <= 12:
        sw = step_data.get("schedule_week")
        return sm, (sw if isinstance(sw, int) and 1 <= sw <= 4 else None)

    # Fall back to week_target string
    week_target = (step_data.get("week_target") or "").lower().strip()
    MONTH_NAMES = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }
    SEASONS = {"spring": 3, "summer": 6, "fall": 9, "winter": 12}

    for name, m in MONTH_NAMES.items():
        if name in week_target:
            return m, None
    for season, m in SEASONS.items():
        if season in week_target:
            return m, None
    if "month 3" in week_target:
        return ((now_month + 1) % 12) + 1, None
    if "month 2" in week_target:
        return (now_month % 12) + 1, None

    # "Immediately", "Week 1-2", "Week 3-4" → current month
    week = None
    if "week 1" in week_target:
        week = 1
    elif "week 3" in week_target:
        week = 3
    return now_month, week


@router.post("/{assessment_id}/add-to-program")
async def add_to_program(assessment_id: int, data: dict = {}, db: AsyncSession = Depends(get_db)):
    """Add the remediation plan's action steps to the active lawn program.

    Accepts optional steps_schedule: list of {ai_order, user_order, month, week_of_month}
    to override AI-inferred timing and apply user-customized ordering.
    """
    from app.models.lawn_program import LawnProgram, LawnProgramStep

    plan_r = await db.execute(select(RemediationPlan).where(RemediationPlan.assessment_id == assessment_id).order_by(desc(RemediationPlan.created_at)).limit(1))
    plan = plan_r.scalar_one_or_none()
    if not plan:
        raise HTTPException(400, "No remediation plan found — run AI analysis first")

    # Build lookup of user schedule overrides keyed by ai_order
    schedule_overrides: dict[int, dict] = {}
    for override in (data.get("steps_schedule") or []):
        schedule_overrides[override["ai_order"]] = override

    # Get or create active program
    program_id = data.get("program_id")
    if program_id:
        prog_r = await db.execute(select(LawnProgram).where(LawnProgram.id == program_id))
        program = prog_r.scalar_one_or_none()
        if not program:
            raise HTTPException(404, "Program not found")
    else:
        prog_r = await db.execute(select(LawnProgram).where(LawnProgram.status == "active").limit(1))
        program = prog_r.scalar_one_or_none()

    if not program:
        year = datetime.now(timezone.utc).year
        program = LawnProgram(
            name=f"Lawn Program {year}",
            season_year=year,
            status="active",
            description="Auto-generated from lawn assessment",
        )
        db.add(program)
        await db.flush()

    # Remove existing AI remediation steps from this plan
    existing_r = await db.execute(select(LawnProgramStep).where(
        LawnProgramStep.program_id == program.id,
        LawnProgramStep.source == "ai_remediation",
        LawnProgramStep.source_ref_id == plan.id,
    ))
    for step in existing_r.scalars().all():
        await db.delete(step)

    now_month = datetime.now(timezone.utc).month

    # If user provided an ordered schedule, process in that order; otherwise use AI order
    action_steps = plan.action_steps or []
    if schedule_overrides:
        # Sort by user_order to determine display order in program
        ordered = sorted(action_steps, key=lambda s: schedule_overrides.get(s.get("order", 0), {}).get("user_order", s.get("order", 99)))
    else:
        ordered = sorted(action_steps, key=lambda s: s.get("order", 99))

    for display_idx, step_data in enumerate(ordered):
        ai_order = step_data.get("order", display_idx + 1)
        override = schedule_overrides.get(ai_order, {})

        if override:
            month = override.get("month") or now_month
            week = override.get("week_of_month")
        else:
            month, week = _resolve_step_month(step_data, now_month)

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
            order_index=(display_idx + 1) * 10,
        )
        db.add(step)

    await db.commit()
    return {"program_id": program.id, "steps_added": len(ordered)}
