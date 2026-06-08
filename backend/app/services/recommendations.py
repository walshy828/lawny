"""Smart lawn care recommendation engine.

Generates watering, mowing, fertilization, and seasonal recommendations
based on weather data, soil temperature, grass type, and location.
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Grass Type Characteristics ─────────────────────
GRASS_PROFILES = {
    # Cool-season grasses
    "kentucky_bluegrass": {
        "season": "cool", "et_rate_in_week": 1.0, "ideal_soil_temp_f": (50, 65),
        "mow_height_in": (2.5, 3.5), "growth_soil_temp_f": 45,
        "fert_soil_temp_f": 55, "dormant_above_f": 90,
    },
    "tall_fescue": {
        "season": "cool", "et_rate_in_week": 0.9, "ideal_soil_temp_f": (50, 65),
        "mow_height_in": (3.0, 4.0), "growth_soil_temp_f": 45,
        "fert_soil_temp_f": 55, "dormant_above_f": 95,
    },
    "fine_fescue": {
        "season": "cool", "et_rate_in_week": 0.7, "ideal_soil_temp_f": (50, 65),
        "mow_height_in": (2.5, 3.5), "growth_soil_temp_f": 45,
        "fert_soil_temp_f": 55, "dormant_above_f": 90,
    },
    "perennial_ryegrass": {
        "season": "cool", "et_rate_in_week": 1.0, "ideal_soil_temp_f": (50, 65),
        "mow_height_in": (2.0, 3.0), "growth_soil_temp_f": 42,
        "fert_soil_temp_f": 55, "dormant_above_f": 90,
    },
    "cool_mix": {
        "season": "cool", "et_rate_in_week": 0.9, "ideal_soil_temp_f": (50, 65),
        "mow_height_in": (2.5, 3.5), "growth_soil_temp_f": 45,
        "fert_soil_temp_f": 55, "dormant_above_f": 90,
    },
    # Warm-season grasses
    "bermuda": {
        "season": "warm", "et_rate_in_week": 1.2, "ideal_soil_temp_f": (65, 85),
        "mow_height_in": (0.5, 2.0), "growth_soil_temp_f": 65,
        "fert_soil_temp_f": 65, "dormant_below_f": 55,
    },
    "zoysia": {
        "season": "warm", "et_rate_in_week": 0.8, "ideal_soil_temp_f": (65, 80),
        "mow_height_in": (1.0, 2.5), "growth_soil_temp_f": 65,
        "fert_soil_temp_f": 65, "dormant_below_f": 55,
    },
    "st_augustine": {
        "season": "warm", "et_rate_in_week": 1.0, "ideal_soil_temp_f": (65, 85),
        "mow_height_in": (2.5, 4.0), "growth_soil_temp_f": 65,
        "fert_soil_temp_f": 65, "dormant_below_f": 55,
    },
    "centipede": {
        "season": "warm", "et_rate_in_week": 0.6, "ideal_soil_temp_f": (65, 80),
        "mow_height_in": (1.5, 2.5), "growth_soil_temp_f": 65,
        "fert_soil_temp_f": 65, "dormant_below_f": 55,
    },
    "buffalo": {
        "season": "warm", "et_rate_in_week": 0.5, "ideal_soil_temp_f": (60, 80),
        "mow_height_in": (2.0, 3.0), "growth_soil_temp_f": 60,
        "fert_soil_temp_f": 60, "dormant_below_f": 50,
    },
    "bahia": {
        "season": "warm", "et_rate_in_week": 0.8, "ideal_soil_temp_f": (65, 85),
        "mow_height_in": (3.0, 4.0), "growth_soil_temp_f": 65,
        "fert_soil_temp_f": 65, "dormant_below_f": 55,
    },
    "warm_mix": {
        "season": "warm", "et_rate_in_week": 0.9, "ideal_soil_temp_f": (65, 85),
        "mow_height_in": (1.5, 3.0), "growth_soil_temp_f": 65,
        "fert_soil_temp_f": 65, "dormant_below_f": 55,
    },
    "mixed_blend": {
        "season": "transition", "et_rate_in_week": 0.9, "ideal_soil_temp_f": (50, 80),
        "mow_height_in": (2.0, 3.5), "growth_soil_temp_f": 50,
        "fert_soil_temp_f": 55, "dormant_below_f": 45,
    },
}

DEFAULT_PROFILE = GRASS_PROFILES["tall_fescue"]


def calculate_adjusted_et_rate(
    grass_type: Optional[str],
    current_temp_f: Optional[float] = None,
    humidity_pct: Optional[float] = None,
    drought_level: Optional[str] = None,
) -> tuple[float, list[str]]:
    """Calculate the temperature/humidity/drought-adjusted ET rate.

    Returns (adjusted_et_rate_inches_per_week, list_of_adjustment_reasons).
    """
    profile = GRASS_PROFILES.get(grass_type, DEFAULT_PROFILE)
    et_rate = profile["et_rate_in_week"]
    reasons = []

    # Temperature adjustment
    if current_temp_f and current_temp_f > 90:
        et_rate *= 1.3
        reasons.append(f"High temp ({current_temp_f}°F) increases water demand")
    elif current_temp_f and current_temp_f > 80:
        et_rate *= 1.1
        reasons.append(f"Warm temp ({current_temp_f}°F) slightly increases water demand")
    elif current_temp_f and current_temp_f < 50:
        et_rate *= 0.4
        reasons.append(f"Cool temp ({current_temp_f}°F) reduces water demand")

    # Humidity adjustment
    if humidity_pct and humidity_pct > 70:
        et_rate *= 0.85
        reasons.append("High humidity reduces evaporation")
    elif humidity_pct and humidity_pct < 30:
        et_rate *= 1.2
        reasons.append("Low humidity increases evaporation")

    # Drought adjustment (conservation)
    if drought_level in ("D2", "D3", "D4"):
        et_rate *= 0.7
        reasons.append(f"Drought condition ({drought_level}) — water conservation recommended")

    return et_rate, reasons


def calculate_daily_need(
    grass_type: Optional[str],
    temp_high_f: Optional[float] = None,
) -> float:
    """Calculate daily water need in inches for a given temperature.

    Returns daily need in inches (weekly ET / 7, adjusted for daily temp).
    """
    profile = GRASS_PROFILES.get(grass_type, DEFAULT_PROFILE)
    base_daily = profile["et_rate_in_week"] / 7.0

    if temp_high_f:
        if temp_high_f > 95:
            base_daily *= 1.4
        elif temp_high_f > 90:
            base_daily *= 1.3
        elif temp_high_f > 85:
            base_daily *= 1.15
        elif temp_high_f > 80:
            base_daily *= 1.05
        elif temp_high_f < 50:
            base_daily *= 0.4
        elif temp_high_f < 60:
            base_daily *= 0.6

    return round(base_daily, 3)


def generate_watering_recommendation(
    grass_type: Optional[str],
    soil_temp_f: Optional[float],
    rain_past_7d_in: float,
    rain_forecast_7d_in: float,
    current_temp_f: Optional[float],
    humidity_pct: Optional[float],
    drought_level: Optional[str],
) -> dict:
    """Generate a watering recommendation based on conditions.

    Returns dict with recommendation, frequency, duration_minutes, and reasoning.
    """
    profile = GRASS_PROFILES.get(grass_type, DEFAULT_PROFILE)
    et_rate = profile["et_rate_in_week"]  # inches per week needed
    reasons = []

    # Adjust ET rate based on temperature
    if current_temp_f and current_temp_f > 90:
        et_rate *= 1.3
        reasons.append(f"High temp ({current_temp_f}°F) increases water demand")
    elif current_temp_f and current_temp_f < 50:
        et_rate *= 0.4
        reasons.append(f"Cool temp ({current_temp_f}°F) reduces water demand")

    # Adjust for humidity
    if humidity_pct and humidity_pct > 70:
        et_rate *= 0.85
        reasons.append("High humidity reduces evaporation")
    elif humidity_pct and humidity_pct < 30:
        et_rate *= 1.2
        reasons.append("Low humidity increases evaporation")

    # Check if grass is dormant
    if soil_temp_f:
        if profile["season"] == "warm" and soil_temp_f < profile.get("dormant_below_f", 55):
            return {
                "recommendation": "none",
                "frequency": "Grass is dormant",
                "duration_minutes": 0,
                "reasoning": f"Soil temperature ({soil_temp_f}°F) indicates {grass_type or 'warm-season'} grass is dormant. No watering needed.",
            }
        elif profile["season"] == "cool" and current_temp_f and current_temp_f > profile.get("dormant_above_f", 90):
            et_rate *= 0.5
            reasons.append("Grass may be entering heat dormancy — reduce watering to avoid disease")

    # Calculate water deficit
    total_natural_water = rain_past_7d_in + rain_forecast_7d_in
    weekly_need = et_rate
    deficit = weekly_need - (total_natural_water / 2)  # Spread across the week

    # Drought adjustment
    if drought_level in ("D2", "D3", "D4"):
        reasons.append(f"Drought condition ({drought_level}) — water conservation recommended")
        deficit *= 0.7  # Reduce recommendation during severe drought

    if drought_level in ("D3", "D4"):
        return {
            "recommendation": "light",
            "frequency": "Every 3 days, early AM only",
            "duration_minutes": 10,
            "reasoning": f"Severe drought ({drought_level}). Water minimally to keep roots alive. " + " ".join(reasons),
        }

    # Generate recommendation
    if deficit <= 0:
        rec = "none"
        freq = "Natural rainfall is sufficient"
        duration = 0
        reasons.append(f"Rain past 7d: {rain_past_7d_in}in + forecast: {rain_forecast_7d_in}in covers the {weekly_need}in/week need")
    elif deficit < 0.3:
        rec = "light"
        freq = "Once this week if no rain"
        duration = 15
        reasons.append(f"Minor water deficit ({deficit:.1f}in). Light supplemental watering recommended")
    elif deficit < 0.6:
        rec = "moderate"
        freq = "Every 2-3 days, early morning"
        duration = 20
        reasons.append(f"Moderate water deficit ({deficit:.1f}in). Regular watering needed")
    elif deficit < 1.0:
        rec = "moderate"
        freq = "Every other day, early morning"
        duration = 25
        reasons.append(f"Significant water deficit ({deficit:.1f}in). Consistent watering schedule needed")
    else:
        rec = "heavy"
        freq = "Daily, early AM (before 10am)"
        duration = 30
        reasons.append(f"High water deficit ({deficit:.1f}in). Daily deep watering recommended")

    return {
        "recommendation": rec,
        "frequency": freq,
        "duration_minutes": duration,
        "reasoning": " | ".join(reasons),
    }


def generate_mowing_recommendation(
    grass_type: Optional[str],
    soil_temp_f: Optional[float],
    days_since_last_mow: Optional[int],
) -> dict:
    """Generate mowing recommendation based on growth conditions."""
    profile = GRASS_PROFILES.get(grass_type, DEFAULT_PROFILE)

    if soil_temp_f and soil_temp_f < profile["growth_soil_temp_f"]:
        return {
            "should_mow": False,
            "reason": f"Soil temp ({soil_temp_f}°F) is below growth threshold ({profile['growth_soil_temp_f']}°F). Grass isn't actively growing.",
            "mow_height": profile["mow_height_in"],
        }

    # Estimate growth rate based on soil temp
    if soil_temp_f:
        ideal_low, ideal_high = profile["ideal_soil_temp_f"]
        if ideal_low <= soil_temp_f <= ideal_high:
            days_between_mows = 5  # Peak growth
        elif soil_temp_f > ideal_high:
            days_between_mows = 10  # Slowed growth in heat
        else:
            days_between_mows = 10  # Cool but growing
    else:
        days_between_mows = 7  # Default weekly

    should_mow = days_since_last_mow is not None and days_since_last_mow >= days_between_mows

    return {
        "should_mow": should_mow,
        "days_between_mows": days_between_mows,
        "days_since_last": days_since_last_mow,
        "reason": f"Based on soil temp and {grass_type or 'grass'} growth rate, mow every ~{days_between_mows} days.",
        "mow_height": profile["mow_height_in"],
    }


def generate_seasonal_tips(
    grass_type: Optional[str],
    soil_temp_f: Optional[float],
    month: int,
) -> list:
    """Generate seasonal lawn care tips."""
    profile = GRASS_PROFILES.get(grass_type, DEFAULT_PROFILE)
    season = profile["season"]
    tips = []

    if season == "cool":
        if month in (3, 4):
            tips.append({"tip": "Apply pre-emergent crabgrass preventer when soil reaches 55°F", "icon": "🧪", "priority": "high" if soil_temp_f and soil_temp_f >= 50 else "info"})
            tips.append({"tip": "Begin mowing when grass starts growing — don't cut more than 1/3 of blade height", "icon": "🔪", "priority": "info"})
        elif month in (5, 6):
            tips.append({"tip": "Raise mowing height for summer heat protection", "icon": "🔪", "priority": "info"})
            tips.append({"tip": "Monitor for grub damage — brown patches that pull up easily", "icon": "🐛", "priority": "info"})
        elif month in (9, 10):
            tips.append({"tip": "Best time to overseed and fertilize cool-season lawns!", "icon": "🌱", "priority": "high"})
            tips.append({"tip": "Aerate before overseeding for best results", "icon": "🌬️", "priority": "high"})
            tips.append({"tip": "Apply fall fertilizer — most important feeding of the year", "icon": "🧪", "priority": "high"})
        elif month in (11, 12):
            tips.append({"tip": "Final mow — lower height slightly to prevent snow mold", "icon": "🔪", "priority": "info"})
            tips.append({"tip": "Apply winterizer fertilizer if not already done", "icon": "🧪", "priority": "info"})
    elif season == "warm":
        if month in (4, 5):
            tips.append({"tip": "Time to apply first fertilizer as grass greens up", "icon": "🧪", "priority": "high" if soil_temp_f and soil_temp_f >= 65 else "info"})
            tips.append({"tip": "Apply pre-emergent for summer annual weeds", "icon": "🧪", "priority": "info"})
        elif month in (6, 7, 8):
            tips.append({"tip": "Peak growing season — maintain consistent mowing schedule", "icon": "🔪", "priority": "info"})
            tips.append({"tip": "Water deeply but infrequently to encourage deep roots", "icon": "💧", "priority": "info"})
        elif month in (9, 10):
            tips.append({"tip": "Last fertilizer application before dormancy", "icon": "🧪", "priority": "info"})
            tips.append({"tip": "Apply post-emergent for winter weeds if needed", "icon": "🧹", "priority": "info"})

    return tips
