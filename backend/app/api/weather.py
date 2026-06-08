"""Weather, forecast, drought, and watering recommendation API."""

from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from app.database import get_db
from app.models import LawnConfig, WateringRecommendation, WeatherSnapshot, DroughtStatus, Activity
from app.services.weather import fetch_current_weather, fetch_forecast, fetch_historical_weather
from app.services.drought import fetch_drought_by_coords, DROUGHT_LEVELS
from app.services.recommendations import (
    generate_watering_recommendation,
    calculate_adjusted_et_rate,
    calculate_daily_need,
    GRASS_PROFILES,
    DEFAULT_PROFILE,
)

router = APIRouter(prefix="/api/weather", tags=["weather"])


async def _get_lawn_location(db: AsyncSession) -> tuple:
    """Get lawn lat/lon or raise 404."""
    result = await db.execute(select(LawnConfig).limit(1))
    lawn = result.scalar_one_or_none()
    if not lawn or not lawn.latitude or not lawn.longitude:
        raise HTTPException(404, "Lawn location not configured. Set your address in Settings first.")
    return lawn.latitude, lawn.longitude, lawn.grass_type


@router.get("/current")
async def current_weather(db: AsyncSession = Depends(get_db)):
    lat, lon, _ = await _get_lawn_location(db)
    return await fetch_current_weather(lat, lon)


@router.get("/forecast")
async def forecast(days: int = 7, db: AsyncSession = Depends(get_db)):
    lat, lon, _ = await _get_lawn_location(db)
    return await fetch_forecast(lat, lon, days)


@router.get("/history")
async def weather_history(days: int = 30, db: AsyncSession = Depends(get_db)):
    lat, lon, _ = await _get_lawn_location(db)
    return await fetch_historical_weather(lat, lon, days)


@router.get("/drought")
async def drought_status(db: AsyncSession = Depends(get_db)):
    lat, lon, _ = await _get_lawn_location(db)

    # Check for cached status first
    cached = await db.execute(select(DroughtStatus).order_by(desc(DroughtStatus.date)).limit(1))
    cached_status = cached.scalar_one_or_none()

    # Fetch fresh if no cache or cache is old
    from datetime import datetime, timedelta
    if not cached_status or (datetime.now() - cached_status.created_at.replace(tzinfo=None)) > timedelta(days=3):
        fresh = await fetch_drought_by_coords(lat, lon)
        if fresh.get("drought_level") is not None or not cached_status:
            ds = DroughtStatus(
                date=datetime.now(),
                drought_level=fresh.get("drought_level"),
                drought_label=fresh.get("drought_label", "Unknown"),
                coverage_pct=fresh.get("coverage_pct"),
                source_data=fresh.get("raw_data"),
            )
            db.add(ds)
            return fresh

    if cached_status:
        return {
            "drought_level": cached_status.drought_level,
            "drought_label": cached_status.drought_label,
            "coverage_pct": cached_status.coverage_pct,
            "last_updated": cached_status.date.isoformat() if cached_status.date else None,
        }

    return {"drought_level": None, "drought_label": "No Data"}


@router.get("/watering")
async def watering_recommendation(db: AsyncSession = Depends(get_db)):
    lat, lon, grass_type = await _get_lawn_location(db)

    # Get current conditions
    current = await fetch_current_weather(lat, lon)
    forecast_data = await fetch_forecast(lat, lon, 7)
    historical = await fetch_historical_weather(lat, lon, 7)

    # Calculate past 7 days rainfall
    rain_past_7d = sum(d.get("precipitation_in", 0) for d in historical)

    # Get drought status
    drought_result = await db.execute(select(DroughtStatus).order_by(desc(DroughtStatus.date)).limit(1))
    drought = drought_result.scalar_one_or_none()
    drought_level = drought.drought_level if drought else None

    rec = generate_watering_recommendation(
        grass_type=grass_type,
        soil_temp_f=current.get("soil_temp_surface_f"),
        rain_past_7d_in=rain_past_7d,
        rain_forecast_7d_in=forecast_data.get("total_precipitation_7d_in", 0),
        current_temp_f=current.get("temperature_f"),
        humidity_pct=current.get("humidity_pct"),
        drought_level=drought_level,
    )

    # Calculate weekly need
    profile = GRASS_PROFILES.get(grass_type, DEFAULT_PROFILE)
    et_rate, _ = calculate_adjusted_et_rate(
        grass_type, current.get("temperature_f"), current.get("humidity_pct"), drought_level
    )

    # Save the recommendation
    wr = WateringRecommendation(
        date=datetime.now(),
        recommendation=rec["recommendation"],
        frequency=rec["frequency"],
        duration_minutes=rec["duration_minutes"],
        reasoning=rec["reasoning"],
        rain_past_7d_in=rain_past_7d,
        rain_forecast_7d_in=forecast_data.get("total_precipitation_7d_in", 0),
        soil_temp_f=current.get("soil_temp_surface_f"),
    )
    db.add(wr)

    # Drought info for response
    drought_info = None
    if drought:
        d_info = DROUGHT_LEVELS.get(drought.drought_level, DROUGHT_LEVELS[None])
        drought_info = {
            "drought_level": drought.drought_level,
            "drought_label": drought.drought_label or d_info["label"],
            "severity": d_info["severity"],
            "color": d_info["color"],
            "coverage_pct": drought.coverage_pct,
        }

    return {
        **rec,
        "rain_past_7d_in": rain_past_7d,
        "rain_forecast_7d_in": forecast_data.get("total_precipitation_7d_in", 0),
        "soil_temp_f": current.get("soil_temp_surface_f"),
        "weekly_need_in": round(et_rate, 2),
        "drought": drought_info,
    }


@router.get("/hydration-balance")
async def hydration_balance(db: AsyncSession = Depends(get_db)):
    """Comprehensive water need vs supply analysis.

    Returns past 7 days actuals + next 7 days forecast with per-day breakdown.
    """
    lat, lon, grass_type = await _get_lawn_location(db)

    # Fetch weather data
    current = await fetch_current_weather(lat, lon)
    forecast_data = await fetch_forecast(lat, lon, 7)
    historical = await fetch_historical_weather(lat, lon, 7)

    # Get drought status
    drought_result = await db.execute(select(DroughtStatus).order_by(desc(DroughtStatus.date)).limit(1))
    drought = drought_result.scalar_one_or_none()
    drought_level = drought.drought_level if drought else None

    # Get logged watering activities from past 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    water_result = await db.execute(
        select(Activity)
        .where(and_(
            Activity.activity_type == "water",
            Activity.date >= seven_days_ago,
        ))
        .order_by(Activity.date)
    )
    water_activities = water_result.scalars().all()

    # Build a date-keyed map of logged watering
    watered_by_date = {}
    for wa in water_activities:
        if wa.date:
            d_key = wa.date.date().isoformat() if hasattr(wa.date, 'date') else str(wa.date)[:10]
            watered_by_date[d_key] = watered_by_date.get(d_key, 0) + (wa.water_amount_inches or 0)

    # ── Past 7 days (actuals) ──
    past_daily = []
    total_rain = 0.0
    total_watered = 0.0
    total_past_need = 0.0

    for day_data in historical:
        d = day_data.get("date", "")
        rain = day_data.get("precipitation_in", 0) or 0
        temp_high = day_data.get("temp_high_f")
        daily_need = calculate_daily_need(grass_type, temp_high)
        watered = watered_by_date.get(d, 0)

        total_rain += rain
        total_watered += watered
        total_past_need += daily_need

        past_daily.append({
            "date": d,
            "rain_in": round(rain, 3),
            "watered_in": round(watered, 3),
            "need_in": round(daily_need, 3),
            "temp_high_f": temp_high,
        })

    # ── Future 7 days (forecast) ──
    future_daily = []
    total_forecast_rain = 0.0
    total_future_need = 0.0

    for day_data in (forecast_data.get("days") or []):
        d = day_data.get("date", "")
        rain = day_data.get("precipitation_in", 0) or 0
        prob = day_data.get("precipitation_probability", 0) or 0
        temp_high = day_data.get("temp_high_f")
        daily_need = calculate_daily_need(grass_type, temp_high)

        # Weight forecast rain by probability
        expected_rain = rain * (prob / 100.0) if prob > 0 else rain * 0.5

        total_forecast_rain += expected_rain
        total_future_need += daily_need

        future_daily.append({
            "date": d,
            "predicted_rain_in": round(expected_rain, 3),
            "raw_rain_in": round(rain, 3),
            "precipitation_probability": prob,
            "predicted_need_in": round(daily_need, 3),
            "temp_high_f": temp_high,
            "weather_code": day_data.get("weather_code"),
        })

    # ── Balance calculation ──
    past_received = total_rain + total_watered
    past_delta = past_received - total_past_need
    projected_delta = (past_received + total_forecast_rain) - (total_past_need + total_future_need)

    if abs(past_delta) < 0.15:
        status = "balanced"
        status_label = "Well Hydrated"
    elif past_delta < 0:
        if past_delta < -0.5:
            status = "under"
            status_label = "Significantly Under-Watered"
        else:
            status = "under"
            status_label = "Slightly Under-Watered"
    else:
        if past_delta > 0.5:
            status = "over"
            status_label = "Significantly Over-Watered"
        else:
            status = "over"
            status_label = "Slightly Over-Watered"

    # ET adjustment factors for transparency
    et_rate, adjustment_reasons = calculate_adjusted_et_rate(
        grass_type,
        current.get("temperature_f"),
        current.get("humidity_pct"),
        drought_level,
    )

    temp_factor = 1.0
    if current.get("temperature_f"):
        t = current["temperature_f"]
        if t > 90: temp_factor = 1.3
        elif t > 80: temp_factor = 1.1
        elif t < 50: temp_factor = 0.4

    humidity_factor = 1.0
    if current.get("humidity_pct"):
        h = current["humidity_pct"]
        if h > 70: humidity_factor = 0.85
        elif h < 30: humidity_factor = 1.2

    # Drought info
    drought_info = None
    if drought:
        d_info = DROUGHT_LEVELS.get(drought.drought_level, DROUGHT_LEVELS[None])
        drought_info = {
            "drought_level": drought.drought_level,
            "drought_label": drought.drought_label or d_info["label"],
            "severity": d_info["severity"],
            "color": d_info["color"],
            "coverage_pct": drought.coverage_pct,
        }

    return {
        "weekly_need_in": round(et_rate, 2),
        "period": {
            "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
        },
        "past": {
            "rain_in": round(total_rain, 2),
            "watering_logged_in": round(total_watered, 2),
            "total_received_in": round(past_received, 2),
            "total_need_in": round(total_past_need, 2),
            "daily": past_daily,
        },
        "future": {
            "predicted_rain_in": round(total_forecast_rain, 2),
            "predicted_need_in": round(total_future_need, 2),
            "shortfall_in": round(max(0.0, total_future_need - total_forecast_rain), 2),
            "daily": future_daily,
        },
        "balance": {
            "past_delta_in": round(past_delta, 2),
            "projected_delta_in": round(projected_delta, 2),
            "forward_delta_in": round(total_forecast_rain - total_future_need, 2),
            "status": status,
            "status_label": status_label,
        },
        "drought": drought_info,
        "adjustments": {
            "temp_factor": temp_factor,
            "humidity_factor": humidity_factor,
            "weekly_et_in": round(et_rate, 2),
            "explanation": " | ".join(adjustment_reasons) if adjustment_reasons else "Standard conditions",
        },
    }
