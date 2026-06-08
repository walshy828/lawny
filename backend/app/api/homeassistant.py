"""Home Assistant integration API.

Provides sensor-friendly endpoints for Home Assistant REST integration.
All endpoints return flat, typed values optimized for HA sensor templates.

Usage in HA configuration.yaml:
  rest:
    - resource: http://lawny-host:8081/api/homeassistant/states
      scan_interval: 300
      sensor:
        - name: "Lawn Watering Recommendation"
          value_template: "{{ value_json.watering_recommendation }}"
          json_attributes:
            - watering_frequency
            - watering_duration_minutes
            - weekly_need_inches
            - rain_past_7d_inches
            - rain_forecast_7d_inches
            - hydration_status
            - hydration_delta_inches
        - name: "Lawn Soil Temperature"
          value_template: "{{ value_json.soil_temp_f }}"
          unit_of_measurement: "°F"
          device_class: temperature
        - name: "Lawn Health Score"
          value_template: "{{ value_json.health_score }}"
        - name: "Lawn Drought Status"
          value_template: "{{ value_json.drought_label }}"
        - name: "Lawn Fertilizer Progress"
          value_template: "{{ value_json.fertilizer_progress_pct }}"
          unit_of_measurement: "%"
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from app.database import get_db
from app.models import (
    LawnConfig, LawnZone, Activity, MaintenanceSchedule,
    WateringRecommendation, WeatherSnapshot, DroughtStatus,
    FertilizerProgram, FertilizerStep, FertilizerApplication,
)
from app.services.weather import fetch_current_weather, fetch_forecast, fetch_historical_weather
from app.services.drought import fetch_drought_by_coords, DROUGHT_LEVELS
from app.services.recommendations import (
    calculate_adjusted_et_rate, calculate_daily_need,
    GRASS_PROFILES, DEFAULT_PROFILE,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/homeassistant", tags=["homeassistant"])


# ── Helper ────────────────────────────────────────────
async def _get_lawn(db: AsyncSession):
    """Get lawn config or None."""
    result = await db.execute(select(LawnConfig).limit(1))
    return result.scalar_one_or_none()


# ── Main States Endpoint ──────────────────────────────
@router.get("/states")
async def ha_states(db: AsyncSession = Depends(get_db)):
    """All Lawny sensor data in a single flat JSON response.

    Designed for Home Assistant REST sensor integration.
    Returns null for unavailable values rather than omitting keys.
    """
    lawn = await _get_lawn(db)

    # Base response with defaults
    state = {
        # ── Lawn Info ──
        "lawn_name": None,
        "grass_type": None,
        "total_sqft": 0,
        "zone_count": 0,
        "has_location": False,

        # ── Weather ──
        "temperature_f": None,
        "feels_like_f": None,
        "humidity_pct": None,
        "wind_speed_mph": None,
        "uv_index": None,
        "soil_temp_f": None,
        "soil_temp_6cm_f": None,
        "sunshine_hours": None,
        "weather_description": None,
        "weather_code": None,

        # ── Watering ──
        "watering_recommendation": None,
        "watering_frequency": None,
        "watering_duration_minutes": None,
        "weekly_need_inches": None,
        "rain_past_7d_inches": None,
        "rain_forecast_7d_inches": None,

        # ── Hydration Balance ──
        "hydration_status": None,
        "hydration_status_label": None,
        "hydration_delta_inches": None,
        "hydration_projected_delta_inches": None,
        "hydration_rain_7d_inches": None,
        "hydration_watered_7d_inches": None,
        "hydration_total_received_inches": None,
        "hydration_total_need_inches": None,

        # ── Drought ──
        "drought_level": None,
        "drought_label": "No Data",
        "drought_severity": 0,
        "drought_color": "#52B788",
        "drought_coverage_pct": None,

        # ── Health & Activity ──
        "health_score": None,
        "last_mow_date": None,
        "days_since_mow": None,
        "last_water_date": None,
        "days_since_water": None,
        "last_fertilize_date": None,
        "days_since_fertilize": None,
        "total_activities": 0,

        # ── Fertilizer ──
        "fertilizer_program_name": None,
        "fertilizer_program_brand": None,
        "fertilizer_progress_pct": 0,
        "fertilizer_completed_steps": 0,
        "fertilizer_total_steps": 0,
        "fertilizer_next_step": None,
        "fertilizer_next_step_month": None,

        # ── Schedule ──
        "next_task_type": None,
        "next_task_days_until": None,
        "next_task_overdue": False,
        "overdue_task_count": 0,

        # ── Meta ──
        "last_updated": datetime.now().isoformat(),
    }

    if not lawn:
        return state

    # ── Lawn Info ──
    zones_result = await db.execute(select(LawnZone).where(LawnZone.lawn_id == lawn.id))
    zones = zones_result.scalars().all()
    total_sqft = sum(z.area_sqft or 0 for z in zones)

    state.update({
        "lawn_name": lawn.name,
        "grass_type": lawn.grass_type,
        "total_sqft": round(total_sqft),
        "zone_count": len(zones),
        "has_location": bool(lawn.latitude and lawn.longitude),
    })

    # ── Weather (current) ──
    if lawn.latitude and lawn.longitude:
        try:
            weather = await fetch_current_weather(lawn.latitude, lawn.longitude)
            if weather:
                state.update({
                    "temperature_f": weather.get("temperature_f"),
                    "feels_like_f": weather.get("feels_like_f"),
                    "humidity_pct": weather.get("humidity_pct"),
                    "wind_speed_mph": weather.get("wind_speed_mph"),
                    "uv_index": weather.get("uv_index"),
                    "soil_temp_f": weather.get("soil_temp_surface_f"),
                    "soil_temp_6cm_f": weather.get("soil_temp_6cm_f"),
                    "sunshine_hours": weather.get("sunshine_hours"),
                    "weather_description": weather.get("weather_description"),
                    "weather_code": weather.get("weather_code"),
                })
        except Exception as e:
            logger.warning(f"HA: weather fetch failed: {e}")

    # ── Watering Recommendation ──
    water_rec = await db.execute(
        select(WateringRecommendation).order_by(desc(WateringRecommendation.date)).limit(1)
    )
    wr = water_rec.scalar_one_or_none()
    if wr:
        state.update({
            "watering_recommendation": wr.recommendation,
            "watering_frequency": wr.frequency,
            "watering_duration_minutes": wr.duration_minutes,
            "rain_past_7d_inches": wr.rain_past_7d_in,
            "rain_forecast_7d_inches": wr.rain_forecast_7d_in,
        })

    # Weekly need
    if lawn.grass_type:
        et_rate, _ = calculate_adjusted_et_rate(
            lawn.grass_type,
            state.get("temperature_f"),
            state.get("humidity_pct"),
        )
        state["weekly_need_inches"] = round(et_rate, 2)

    # ── Hydration Balance ──
    if lawn.latitude and lawn.longitude and lawn.grass_type:
        try:
            historical = await fetch_historical_weather(lawn.latitude, lawn.longitude, 7)
            forecast_data = await fetch_forecast(lawn.latitude, lawn.longitude, 7)

            # Past rain
            total_rain = sum(d.get("precipitation_in", 0) or 0 for d in historical)

            # Logged watering
            seven_days_ago = datetime.now() - timedelta(days=7)
            water_acts = await db.execute(
                select(func.coalesce(func.sum(Activity.water_amount_inches), 0))
                .where(and_(
                    Activity.activity_type == "water",
                    Activity.date >= seven_days_ago,
                ))
            )
            total_watered = float(water_acts.scalar_one_or_none() or 0)

            # Compute needs
            total_past_need = sum(
                calculate_daily_need(lawn.grass_type, d.get("temp_high_f"))
                for d in historical
            )
            total_future_need = sum(
                calculate_daily_need(lawn.grass_type, d.get("temp_high_f"))
                for d in (forecast_data.get("days") or [])
            )
            forecast_rain = sum(
                (d.get("precipitation_in", 0) or 0) * ((d.get("precipitation_probability", 50) or 50) / 100.0)
                for d in (forecast_data.get("days") or [])
            )

            past_received = total_rain + total_watered
            past_delta = past_received - total_past_need
            projected_delta = (past_received + forecast_rain) - (total_past_need + total_future_need)

            if abs(past_delta) < 0.15:
                h_status = "balanced"
                h_label = "Well Hydrated"
            elif past_delta < -0.5:
                h_status = "under"
                h_label = "Significantly Under-Watered"
            elif past_delta < 0:
                h_status = "under"
                h_label = "Slightly Under-Watered"
            elif past_delta > 0.5:
                h_status = "over"
                h_label = "Significantly Over-Watered"
            else:
                h_status = "over"
                h_label = "Slightly Over-Watered"

            state.update({
                "hydration_status": h_status,
                "hydration_status_label": h_label,
                "hydration_delta_inches": round(past_delta, 2),
                "hydration_projected_delta_inches": round(projected_delta, 2),
                "hydration_rain_7d_inches": round(total_rain, 2),
                "hydration_watered_7d_inches": round(total_watered, 2),
                "hydration_total_received_inches": round(past_received, 2),
                "hydration_total_need_inches": round(total_past_need, 2),
            })
        except Exception as e:
            logger.warning(f"HA: hydration calc failed: {e}")

    # ── Drought ──
    drought_r = await db.execute(select(DroughtStatus).order_by(desc(DroughtStatus.date)).limit(1))
    drought = drought_r.scalar_one_or_none()
    if drought:
        d_info = DROUGHT_LEVELS.get(drought.drought_level, DROUGHT_LEVELS[None])
        state.update({
            "drought_level": drought.drought_level,
            "drought_label": drought.drought_label or d_info["label"],
            "drought_severity": d_info["severity"],
            "drought_color": d_info["color"],
            "drought_coverage_pct": drought.coverage_pct,
        })

    # ── Health & Activity Stats ──
    now = datetime.now()

    # Average health
    avg_r = await db.execute(
        select(func.avg(Activity.health_score)).where(Activity.health_score.isnot(None))
    )
    avg_health = avg_r.scalar_one_or_none()
    if avg_health:
        state["health_score"] = round(float(avg_health), 1)

    # Total activities
    total_r = await db.execute(select(func.count()).select_from(Activity))
    state["total_activities"] = total_r.scalar_one_or_none() or 0

    # Last mow
    mow_r = await db.execute(
        select(Activity.date).where(Activity.activity_type == "mow")
        .order_by(desc(Activity.date)).limit(1)
    )
    last_mow = mow_r.scalar_one_or_none()
    if last_mow:
        state["last_mow_date"] = last_mow.isoformat()
        state["days_since_mow"] = (now - last_mow.replace(tzinfo=None)).days

    # Last water
    water_r = await db.execute(
        select(Activity.date).where(Activity.activity_type == "water")
        .order_by(desc(Activity.date)).limit(1)
    )
    last_water = water_r.scalar_one_or_none()
    if last_water:
        state["last_water_date"] = last_water.isoformat()
        state["days_since_water"] = (now - last_water.replace(tzinfo=None)).days

    # Last fertilize
    fert_r = await db.execute(
        select(Activity.date).where(Activity.activity_type == "fertilize")
        .order_by(desc(Activity.date)).limit(1)
    )
    last_fert = fert_r.scalar_one_or_none()
    if last_fert:
        state["last_fertilize_date"] = last_fert.isoformat()
        state["days_since_fertilize"] = (now - last_fert.replace(tzinfo=None)).days

    # ── Fertilizer Program ──
    if lawn.active_program_id:
        try:
            prog_r = await db.execute(
                select(FertilizerProgram).where(FertilizerProgram.id == lawn.active_program_id)
            )
            program = prog_r.scalar_one_or_none()
            if program:
                steps_r = await db.execute(
                    select(FertilizerStep).where(FertilizerStep.program_id == program.id)
                    .order_by(FertilizerStep.step_number)
                )
                steps = steps_r.scalars().all()

                # Count completed
                apps_r = await db.execute(
                    select(FertilizerApplication).where(and_(
                        FertilizerApplication.lawn_id == lawn.id,
                        FertilizerApplication.status == "applied",
                    ))
                )
                completed_step_ids = {a.step_id for a in apps_r.scalars().all()}
                completed = sum(1 for s in steps if s.id in completed_step_ids)
                total = len(steps)
                pct = round((completed / total) * 100) if total > 0 else 0

                # Find next step
                current_month = now.month
                next_step_name = None
                next_step_month = None
                for s in steps:
                    if s.id not in completed_step_ids:
                        next_step_name = s.product_name
                        next_step_month = s.month_start
                        break

                state.update({
                    "fertilizer_program_name": program.name,
                    "fertilizer_program_brand": program.brand,
                    "fertilizer_progress_pct": pct,
                    "fertilizer_completed_steps": completed,
                    "fertilizer_total_steps": total,
                    "fertilizer_next_step": next_step_name,
                    "fertilizer_next_step_month": next_step_month,
                })
        except Exception as e:
            logger.warning(f"HA: fertilizer fetch failed: {e}")

    # ── Upcoming Schedules ──
    sched_r = await db.execute(
        select(MaintenanceSchedule).where(MaintenanceSchedule.is_active == True)
        .order_by(MaintenanceSchedule.next_due)
    )
    schedules = sched_r.scalars().all()
    overdue_count = 0
    for s in schedules:
        if s.next_due:
            days_until = (s.next_due.replace(tzinfo=None) - now).days if s.next_due.tzinfo else (s.next_due - now).days
            if days_until < 0:
                overdue_count += 1
            if state["next_task_type"] is None:
                state["next_task_type"] = s.activity_type
                state["next_task_days_until"] = days_until
                state["next_task_overdue"] = days_until < 0
    state["overdue_task_count"] = overdue_count

    return state


# ── Watering Detail Endpoint ──────────────────────────
@router.get("/watering")
async def ha_watering(db: AsyncSession = Depends(get_db)):
    """Detailed watering plan data for HA sensors.

    Returns current recommendation, hydration balance per-day breakdown,
    and forecast data.
    """
    lawn = await _get_lawn(db)
    if not lawn or not lawn.latitude or not lawn.longitude:
        return {"error": "Lawn location not configured"}

    try:
        current = await fetch_current_weather(lawn.latitude, lawn.longitude)
        forecast_data = await fetch_forecast(lawn.latitude, lawn.longitude, 7)
        historical = await fetch_historical_weather(lawn.latitude, lawn.longitude, 7)
    except Exception as e:
        return {"error": f"Weather fetch failed: {e}"}

    grass = lawn.grass_type
    et_rate, reasons = calculate_adjusted_et_rate(
        grass, current.get("temperature_f"), current.get("humidity_pct")
    )

    # Past 7d rainfall
    rain_past_7d = sum(d.get("precipitation_in", 0) or 0 for d in historical)

    # Logged watering
    seven_days_ago = datetime.now() - timedelta(days=7)
    water_acts = await db.execute(
        select(Activity).where(and_(
            Activity.activity_type == "water",
            Activity.date >= seven_days_ago,
        )).order_by(Activity.date)
    )
    activities = water_acts.scalars().all()
    watered_by_date = {}
    for wa in activities:
        if wa.date:
            d_key = wa.date.date().isoformat() if hasattr(wa.date, 'date') else str(wa.date)[:10]
            watered_by_date[d_key] = watered_by_date.get(d_key, 0) + (wa.water_amount_inches or 0)
    total_watered = sum(watered_by_date.values())

    # Latest recommendation
    rec_r = await db.execute(
        select(WateringRecommendation).order_by(desc(WateringRecommendation.date)).limit(1)
    )
    rec = rec_r.scalar_one_or_none()

    # Per-day past breakdown
    past_days = []
    for d in historical:
        date_str = d.get("date", "")
        past_days.append({
            "date": date_str,
            "rain_inches": round(d.get("precipitation_in", 0) or 0, 3),
            "watered_inches": round(watered_by_date.get(date_str, 0), 3),
            "need_inches": round(calculate_daily_need(grass, d.get("temp_high_f")), 3),
            "temp_high_f": d.get("temp_high_f"),
        })

    # Per-day forecast
    forecast_days = []
    for d in (forecast_data.get("days") or []):
        prob = d.get("precipitation_probability", 50) or 50
        rain = d.get("precipitation_in", 0) or 0
        forecast_days.append({
            "date": d.get("date", ""),
            "predicted_rain_inches": round(rain * (prob / 100.0), 3),
            "rain_probability_pct": prob,
            "need_inches": round(calculate_daily_need(grass, d.get("temp_high_f")), 3),
            "temp_high_f": d.get("temp_high_f"),
            "weather_description": d.get("weather_description", ""),
        })

    total_past_need = sum(d["need_inches"] for d in past_days)
    past_delta = (rain_past_7d + total_watered) - total_past_need

    return {
        "recommendation": rec.recommendation if rec else None,
        "frequency": rec.frequency if rec else None,
        "duration_minutes": rec.duration_minutes if rec else None,
        "weekly_need_inches": round(et_rate, 2),
        "rain_past_7d_inches": round(rain_past_7d, 2),
        "watered_past_7d_inches": round(total_watered, 2),
        "total_received_inches": round(rain_past_7d + total_watered, 2),
        "total_need_inches": round(total_past_need, 2),
        "delta_inches": round(past_delta, 2),
        "soil_temp_f": current.get("soil_temp_surface_f"),
        "adjustments": " | ".join(reasons) if reasons else "Standard conditions",
        "past_daily": past_days,
        "forecast_daily": forecast_days,
        "last_updated": datetime.now().isoformat(),
    }


# ── Fertilizer Detail Endpoint ────────────────────────
@router.get("/fertilizer")
async def ha_fertilizer(db: AsyncSession = Depends(get_db)):
    """Fertilizer program status for HA sensors."""
    lawn = await _get_lawn(db)
    if not lawn or not lawn.active_program_id:
        return {
            "active": False,
            "program_name": None,
            "brand": None,
            "progress_pct": 0,
            "completed_steps": 0,
            "total_steps": 0,
            "next_step": None,
            "steps": [],
        }

    prog_r = await db.execute(
        select(FertilizerProgram).where(FertilizerProgram.id == lawn.active_program_id)
    )
    program = prog_r.scalar_one_or_none()
    if not program:
        return {"active": False, "program_name": None}

    steps_r = await db.execute(
        select(FertilizerStep).where(FertilizerStep.program_id == program.id)
        .order_by(FertilizerStep.step_number)
    )
    steps = steps_r.scalars().all()

    apps_r = await db.execute(
        select(FertilizerApplication).where(and_(
            FertilizerApplication.lawn_id == lawn.id,
            FertilizerApplication.status == "applied",
        ))
    )
    completed_step_ids = {a.step_id for a in apps_r.scalars().all()}
    completed = sum(1 for s in steps if s.id in completed_step_ids)
    total = len(steps)
    pct = round((completed / total) * 100) if total > 0 else 0

    step_list = []
    next_step = None
    for s in steps:
        is_done = s.id in completed_step_ids
        step_info = {
            "step_number": s.step_number,
            "product_name": s.product_name,
            "season": s.season,
            "month_start": s.month_start,
            "month_end": s.month_end,
            "status": "applied" if is_done else "pending",
            "application_rate": s.application_rate_per_1k,
        }
        step_list.append(step_info)
        if not is_done and next_step is None:
            next_step = s.product_name

    return {
        "active": True,
        "program_name": program.name,
        "brand": program.brand,
        "progress_pct": pct,
        "completed_steps": completed,
        "total_steps": total,
        "next_step": next_step,
        "steps": step_list,
        "last_updated": datetime.now().isoformat(),
    }


# ── Recent Activities Endpoint ─────────────────────────
@router.get("/activities")
async def ha_activities(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Recent activity log for HA sensors."""
    result = await db.execute(
        select(Activity).order_by(desc(Activity.date)).limit(limit)
    )
    activities = result.scalars().all()

    items = []
    for a in activities:
        zone_name = None
        if a.zone_id:
            zr = await db.execute(select(LawnZone.name).where(LawnZone.id == a.zone_id))
            zone_name = zr.scalar_one_or_none()
        items.append({
            "id": a.id,
            "type": a.activity_type,
            "date": a.date.isoformat() if a.date else None,
            "zone": zone_name,
            "health_score": a.health_score,
            "water_amount_inches": a.water_amount_inches,
            "notes": a.notes,
        })

    return {"activities": items, "count": len(items)}
