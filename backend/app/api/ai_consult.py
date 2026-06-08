"""AI Consultation API — context-aware lawn care Q&A and seasonal alerts."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models import (
    AIConsultation, LawnConfig, LawnZone, SoilTest, Observation,
    Activity, WateringRecommendation, DroughtStatus, WeatherSnapshot,
)
from app.services.ai_provider import get_provider, safe_consult, db_config_from_lawn, is_provider_enabled
from app.services.seasonal_calendar import get_active_alerts
from app.config import settings

router = APIRouter(prefix="/api/ai", tags=["ai"])
logger = logging.getLogger(__name__)


async def _build_context(db: AsyncSession, observation_ids: list[int] = None, zone_id: int = None) -> dict:
    """Assemble a rich context bundle for AI consultation."""
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()

    zones_r = await db.execute(select(LawnZone))
    zones = zones_r.scalars().all()
    total_sqft = sum(z.area_sqft or 0 for z in zones)

    # Latest soil test
    soil_r = await db.execute(select(SoilTest).order_by(desc(SoilTest.test_date)).limit(1))
    soil = soil_r.scalar_one_or_none()

    # Active observations
    obs_q = select(Observation).where(Observation.status.in_(["active", "monitoring"])).order_by(desc(Observation.date)).limit(10)
    obs_r = await db.execute(obs_q)
    observations = obs_r.scalars().all()

    # If specific observation IDs were requested, add those too
    specific_obs = []
    if observation_ids:
        for oid in observation_ids:
            r = await db.execute(select(Observation).where(Observation.id == oid))
            o = r.scalar_one_or_none()
            if o:
                specific_obs.append(o)

    # Recent activities (last 30 days)
    activities_r = await db.execute(
        select(Activity).order_by(desc(Activity.date)).limit(15)
    )
    activities = activities_r.scalars().all()

    # Latest weather
    weather_r = await db.execute(select(WeatherSnapshot).order_by(desc(WeatherSnapshot.date)).limit(1))
    weather = weather_r.scalar_one_or_none()

    # Latest watering recommendation
    water_r = await db.execute(select(WateringRecommendation).order_by(desc(WateringRecommendation.date)).limit(1))
    water_rec = water_r.scalar_one_or_none()

    # Latest drought
    drought_r = await db.execute(select(DroughtStatus).order_by(desc(DroughtStatus.date)).limit(1))
    drought = drought_r.scalar_one_or_none()

    # Seasonal alerts for current month
    now = datetime.now()
    seasonal_alerts = get_active_alerts(
        month=now.month,
        lat=lawn.latitude if lawn else None,
        lon=lawn.longitude if lawn else None,
        grass_type=lawn.grass_type if lawn else None,
    ) if lawn else []

    context = {
        "lawn": {
            "name": lawn.name if lawn else "Unknown",
            "address": lawn.address if lawn else None,
            "grass_type": lawn.grass_type if lawn else None,
            "climate_zone": lawn.climate_zone if lawn else None,
            "usda_zone": lawn.usda_zone if lawn else None,
            "total_sqft": round(total_sqft, 0),
            "zone_count": len(zones),
        },
        "soil_test": {
            "date": soil.test_date.strftime("%Y-%m-%d") if soil else None,
            "ph": soil.ph if soil else None,
            "phosphorus_ppm": soil.phosphorus_ppm if soil else None,
            "potassium_ppm": soil.potassium_ppm if soil else None,
            "organic_matter_pct": soil.organic_matter_pct if soil else None,
            "notes": soil.notes if soil else None,
        } if soil else None,
        "active_observations": [
            {
                "type": o.observation_type,
                "severity": o.severity,
                "coverage_pct": o.coverage_pct,
                "description": o.description,
                "date": o.date.strftime("%Y-%m-%d") if o.date else None,
                "status": o.status,
            }
            for o in (specific_obs + [o for o in observations if o.id not in [s.id for s in specific_obs]])
        ],
        "recent_activities": [
            {
                "type": a.activity_type,
                "date": a.date.strftime("%Y-%m-%d") if a.date else None,
                "health_score": a.health_score,
                "notes": a.notes,
                "products_used": a.products_used,
            }
            for a in activities[:10]
        ],
        "weather": {
            "temp_f": weather.temp_high_f if weather else None,
            "soil_temp_f": weather.soil_temp_0cm_f if weather else None,
            "humidity_pct": weather.humidity_pct if weather else None,
            "uv_index": weather.uv_index if weather else None,
            "date": weather.date.strftime("%Y-%m-%d") if weather else None,
        } if weather else None,
        "watering_recommendation": water_rec.recommendation if water_rec else None,
        "drought_level": drought.drought_level if drought else None,
        "current_month": now.month,
        "current_date": now.strftime("%Y-%m-%d"),
        "seasonal_alerts_active": [a["name"] for a in seasonal_alerts[:5]],
    }

    return context


def _format_context_for_ai(context: dict, question: str) -> str:
    """Format the context bundle into a natural language message for the AI."""
    parts = [f"Question: {question}", "", "Lawn Context:"]

    lawn = context.get("lawn", {})
    parts.append(f"- Lawn: {lawn.get('name')}, {lawn.get('total_sqft', 0):.0f} sqft, {lawn.get('zone_count', 0)} zones")
    parts.append(f"- Grass type: {lawn.get('grass_type') or 'unknown'}")
    parts.append(f"- Location/address: {lawn.get('address') or 'not set'}")
    if lawn.get("usda_zone"):
        parts.append(f"- USDA zone: {lawn['usda_zone']}")

    if context.get("soil_test"):
        soil = context["soil_test"]
        parts.append(f"\nSoil Test (dated {soil.get('date')}):")
        if soil.get("ph"):
            parts.append(f"- pH: {soil['ph']}")
        if soil.get("phosphorus_ppm"):
            parts.append(f"- Phosphorus: {soil['phosphorus_ppm']} ppm")
        if soil.get("potassium_ppm"):
            parts.append(f"- Potassium: {soil['potassium_ppm']} ppm")
        if soil.get("organic_matter_pct"):
            parts.append(f"- Organic matter: {soil['organic_matter_pct']}%")
    else:
        parts.append("\nSoil Test: No soil test data available")

    obs = context.get("active_observations", [])
    if obs:
        parts.append(f"\nActive Observations ({len(obs)} issues):")
        for o in obs[:6]:
            parts.append(f"- {o['type']} ({o.get('severity', 'unknown')} severity, {o.get('coverage_pct', '?')}% coverage): {o.get('description') or 'no description'}")
    else:
        parts.append("\nActive Observations: None logged")

    recent = context.get("recent_activities", [])
    if recent:
        parts.append(f"\nRecent Activities (last {len(recent)}):")
        for a in recent[:6]:
            parts.append(f"- {a['type']} on {a.get('date')} (health score: {a.get('health_score') or 'not rated'})")
            if a.get("notes"):
                parts.append(f"  Notes: {a['notes'][:100]}")

    weather = context.get("weather")
    if weather:
        parts.append(f"\nCurrent Weather: {weather.get('temp_f')}°F air temp, {weather.get('soil_temp_f')}°F soil temp, {weather.get('humidity_pct')}% humidity")

    if context.get("drought_level") and context["drought_level"] not in (None, "None"):
        parts.append(f"Drought level: {context['drought_level']}")

    if context.get("watering_recommendation"):
        parts.append(f"Watering recommendation: {context['watering_recommendation']}")

    alerts = context.get("seasonal_alerts_active", [])
    if alerts:
        parts.append(f"\nActive Seasonal Alerts for current month:")
        for a in alerts:
            parts.append(f"- {a}")

    parts.append(f"\nCurrent date: {context.get('current_date')}")

    return "\n".join(parts)


@router.post("/consult")
async def ai_consult(data: dict, db: AsyncSession = Depends(get_db)):
    """Generate a context-aware AI lawn care recommendation."""
    question = data.get("question", "").strip()
    if not question:
        raise HTTPException(400, "question is required")

    # Get the selected provider from lawn config
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    provider_name = lawn.ai_provider if lawn and lawn.ai_provider else "openai"
    db_cfg = db_config_from_lawn(lawn)
    if not any(is_provider_enabled(p, db_cfg) for p in ("openai", "anthropic", "gemini")):
        raise HTTPException(400, "No AI provider configured. Add an API key in Settings → AI Configuration.")

    provider = get_provider(data.get("ai_provider") or provider_name, db_config=db_cfg)
    observation_ids = data.get("observation_ids", [])
    zone_id = data.get("zone_id")

    context = await _build_context(db, observation_ids=observation_ids, zone_id=zone_id)
    user_message = _format_context_for_ai(context, question)

    try:
        structured, raw = await safe_consult(provider, user_message)
    except Exception as e:
        logger.error(f"AI consult failed: {e}")
        raise HTTPException(500, f"AI consultation failed: {str(e)}")

    consultation = AIConsultation(
        question=question,
        context_snapshot=context,
        response_text=raw,
        structured_response=structured,
        ai_provider=provider.provider_name,
        ai_model=provider.model_name,
        observation_ids=observation_ids or None,
        zone_id=zone_id,
    )
    db.add(consultation)
    await db.flush()

    return {
        "id": consultation.id,
        "question": question,
        "summary": structured.get("summary", raw[:500] if raw else ""),
        "root_cause": structured.get("root_cause"),
        "immediate_actions": structured.get("immediate_actions", []),
        "products": structured.get("products", []),
        "prevention": structured.get("prevention"),
        "expected_timeline": structured.get("expected_timeline"),
        "watch_for": structured.get("watch_for"),
        "ai_provider": provider.provider_name,
        "ai_model": provider.model_name,
    }


@router.get("/consultations")
async def list_consultations(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AIConsultation).order_by(desc(AIConsultation.created_at)).limit(limit)
    )
    items = []
    for c in result.scalars().all():
        items.append({
            "id": c.id,
            "question": c.question[:120] + ("..." if len(c.question) > 120 else ""),
            "summary": (c.structured_response or {}).get("summary", "")[:200] if c.structured_response else "",
            "ai_provider": c.ai_provider,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return items


@router.get("/consultations/{consult_id}")
async def get_consultation(consult_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIConsultation).where(AIConsultation.id == consult_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Consultation not found")

    structured = c.structured_response or {}
    return {
        "id": c.id,
        "question": c.question,
        "summary": structured.get("summary", c.response_text[:500] if c.response_text else ""),
        "root_cause": structured.get("root_cause"),
        "immediate_actions": structured.get("immediate_actions", []),
        "products": structured.get("products", []),
        "prevention": structured.get("prevention"),
        "expected_timeline": structured.get("expected_timeline"),
        "watch_for": structured.get("watch_for"),
        "ai_provider": c.ai_provider,
        "ai_model": c.ai_model,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("/seasonal-alerts")
async def get_seasonal_alerts(db: AsyncSession = Depends(get_db)):
    """Return active seasonal alerts for the current month and lawn location."""
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()

    now = datetime.now()
    alerts = get_active_alerts(
        month=now.month,
        lat=lawn.latitude if lawn else None,
        lon=lawn.longitude if lawn else None,
        grass_type=lawn.grass_type if lawn else None,
    )
    return {"month": now.month, "alerts": alerts, "count": len(alerts)}


@router.get("/providers")
async def get_ai_providers(db: AsyncSession = Depends(get_db)):
    """Return which AI providers are configured (DB key or env var) with active models."""
    from app.services.ai_provider import is_provider_enabled, db_config_from_lawn, AVAILABLE_MODELS, DEFAULT_MODELS, _mask_key
    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    db_cfg = db_config_from_lawn(lawn)

    result = {}
    for p in ("openai", "anthropic", "gemini"):
        enabled = is_provider_enabled(p, db_cfg)
        db_key = db_cfg.get(f"{p}_api_key")
        env_key = getattr(settings, f"{p.upper()}_API_KEY", None)
        model = db_cfg.get(f"{p}_model") or DEFAULT_MODELS[p]
        result[p] = {
            "enabled": enabled,
            "model": model,
            "key_source": "database" if db_key else ("environment" if env_key else None),
            "key_masked": _mask_key(db_key or env_key),
            "available_models": AVAILABLE_MODELS[p],
        }
    result["any_enabled"] = any(v["enabled"] for v in result.values())
    return result


@router.get("/models")
async def get_ai_models(provider: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch available models from the provider's live API.
    Falls back to the hardcoded AVAILABLE_MODELS list if the API call fails
    or the provider isn't configured.
    """
    from app.services.ai_provider import (
        get_provider, db_config_from_lawn, AVAILABLE_MODELS, is_provider_enabled
    )
    if provider not in ("openai", "anthropic", "gemini"):
        raise HTTPException(400, f"Unknown provider: {provider}")

    lawn_r = await db.execute(select(LawnConfig).limit(1))
    lawn = lawn_r.scalar_one_or_none()
    db_cfg = db_config_from_lawn(lawn)

    if not is_provider_enabled(provider, db_cfg):
        return {"provider": provider, "models": AVAILABLE_MODELS[provider], "source": "fallback"}

    p = get_provider(provider, db_config=db_cfg)
    live_models = await p.list_models()

    if live_models:
        return {"provider": provider, "models": live_models, "source": "live"}
    return {"provider": provider, "models": AVAILABLE_MODELS[provider], "source": "fallback"}
