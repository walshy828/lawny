"""Open-Meteo weather integration — no API key required!

Provides current weather, forecasts, soil temperature, and historical data.
API docs: https://open-meteo.com/en/docs
"""

import httpx
import logging
from datetime import datetime, timedelta, date
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://api.open-meteo.com/v1"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1"

# WMO Weather Codes to descriptions
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ slight hail", 99: "Thunderstorm w/ heavy hail",
}


def _c_to_f(c: Optional[float]) -> Optional[float]:
    """Convert Celsius to Fahrenheit."""
    if c is None:
        return None
    return round(c * 9 / 5 + 32, 1)


def _mm_to_in(mm: Optional[float]) -> Optional[float]:
    """Convert millimeters to inches."""
    if mm is None:
        return None
    return round(mm / 25.4, 2)


def _kmh_to_mph(kmh: Optional[float]) -> Optional[float]:
    """Convert km/h to mph."""
    if kmh is None:
        return None
    return round(kmh * 0.621371, 1)


async def geocode_address(query: str) -> Optional[dict]:
    """Geocode an address string to lat/lon using Nominatim (OpenStreetMap).

    Nominatim supports full street addresses unlike Open-Meteo which only
    handles city/place names.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://nominatim.openstreetmap.org/search", params={
                "q": query, "format": "json", "limit": 1, "addressdetails": 1,
            }, headers={"User-Agent": "Lawny/1.0"})
            resp.raise_for_status()
            data = resp.json()
            if data and len(data) > 0:
                r = data[0]
                addr = r.get("address", {})
                return {
                    "latitude": float(r["lat"]),
                    "longitude": float(r["lon"]),
                    "display_name": r.get("display_name", ""),
                    "name": addr.get("road", addr.get("city", "")),
                    "city": addr.get("city", addr.get("town", addr.get("village", ""))),
                    "state": addr.get("state", ""),
                    "country": addr.get("country", ""),
                    "postcode": addr.get("postcode", ""),
                }
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
    return None


async def fetch_current_weather(lat: float, lon: float) -> dict:
    """Fetch current weather conditions + soil temperature."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/forecast", params={
                "latitude": lat,
                "longitude": lon,
                "current": ",".join([
                    "temperature_2m", "apparent_temperature", "relative_humidity_2m",
                    "precipitation", "weather_code", "wind_speed_10m",
                    "uv_index",
                ]),
                "hourly": "soil_temperature_0cm,soil_temperature_6cm,sunshine_duration",
                "daily": "sunshine_duration,uv_index_max",
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm",
                "timezone": "auto",
                "forecast_days": 1,
            })
            resp.raise_for_status()
            data = resp.json()

            current = data.get("current", {})
            hourly = data.get("hourly", {})

            # Get current hour soil temps
            now_hour = datetime.now().hour
            soil_0 = hourly.get("soil_temperature_0cm", [None] * 24)
            soil_6 = hourly.get("soil_temperature_6cm", [None] * 24)
            sunshine = hourly.get("sunshine_duration", [0] * 24)

            # Sum sunshine so far today (seconds -> hours)
            total_sunshine_s = sum(s for s in sunshine[:now_hour + 1] if s)

            daily = data.get("daily", {})
            uv_max = daily.get("uv_index_max", [None])[0] if daily.get("uv_index_max") else None

            return {
                "temperature_f": _c_to_f(current.get("temperature_2m")),
                "feels_like_f": _c_to_f(current.get("apparent_temperature")),
                "humidity_pct": current.get("relative_humidity_2m"),
                "wind_speed_mph": _kmh_to_mph(current.get("wind_speed_10m")),
                "precipitation_in": _mm_to_in(current.get("precipitation")),
                "uv_index": current.get("uv_index") or uv_max,
                "soil_temp_surface_f": _c_to_f(soil_0[min(now_hour, len(soil_0) - 1)] if soil_0 else None),
                "soil_temp_6cm_f": _c_to_f(soil_6[min(now_hour, len(soil_6) - 1)] if soil_6 else None),
                "sunshine_hours": round(total_sunshine_s / 3600, 1) if total_sunshine_s else 0,
                "weather_code": current.get("weather_code"),
                "weather_description": WMO_CODES.get(current.get("weather_code", -1), "Unknown"),
                "timestamp": current.get("time"),
                "raw": data,
            }
    except Exception as e:
        logger.error(f"Weather fetch failed: {e}")
        return {}


async def fetch_forecast(lat: float, lon: float, days: int = 7) -> dict:
    """Fetch multi-day forecast with precipitation and sunshine."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/forecast", params={
                "latitude": lat,
                "longitude": lon,
                "daily": ",".join([
                    "temperature_2m_max", "temperature_2m_min",
                    "precipitation_sum", "precipitation_probability_max",
                    "weather_code", "sunshine_duration", "uv_index_max",
                ]),
                "temperature_unit": "celsius",
                "precipitation_unit": "mm",
                "timezone": "auto",
                "forecast_days": days,
            })
            resp.raise_for_status()
            data = resp.json()
            daily = data.get("daily", {})

            forecast_days = []
            total_precip = 0
            dates = daily.get("time", [])

            for i, d in enumerate(dates):
                precip = daily.get("precipitation_sum", [0])[i] or 0
                total_precip += precip
                wcode = daily.get("weather_code", [0])[i]
                sunshine_s = daily.get("sunshine_duration", [0])[i] or 0

                forecast_days.append({
                    "date": d,
                    "temp_high_f": _c_to_f(daily.get("temperature_2m_max", [None])[i]),
                    "temp_low_f": _c_to_f(daily.get("temperature_2m_min", [None])[i]),
                    "precipitation_in": _mm_to_in(precip),
                    "precipitation_probability": daily.get("precipitation_probability_max", [0])[i],
                    "weather_code": wcode,
                    "weather_description": WMO_CODES.get(wcode, "Unknown"),
                    "sunshine_hours": round(sunshine_s / 3600, 1),
                    "uv_index_max": daily.get("uv_index_max", [None])[i],
                })

            return {
                "days": forecast_days,
                "total_precipitation_7d_in": _mm_to_in(total_precip),
            }
    except Exception as e:
        logger.error(f"Forecast fetch failed: {e}")
        return {"days": [], "total_precipitation_7d_in": 0}


async def fetch_historical_weather(lat: float, lon: float, days: int = 30) -> list:
    """Fetch past weather data for trend analysis."""
    try:
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=days)

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BASE_URL}/forecast", params={
                "latitude": lat,
                "longitude": lon,
                "daily": ",".join([
                    "temperature_2m_max", "temperature_2m_min",
                    "precipitation_sum", "sunshine_duration",
                ]),
                "temperature_unit": "celsius",
                "precipitation_unit": "mm",
                "timezone": "auto",
                "past_days": days,
                "forecast_days": 0,
            })
            resp.raise_for_status()
            data = resp.json()
            daily = data.get("daily", {})

            results = []
            for i, d in enumerate(daily.get("time", [])):
                results.append({
                    "date": d,
                    "temp_high_f": _c_to_f(daily.get("temperature_2m_max", [None])[i]),
                    "temp_low_f": _c_to_f(daily.get("temperature_2m_min", [None])[i]),
                    "precipitation_in": _mm_to_in(daily.get("precipitation_sum", [0])[i] or 0),
                    "sunshine_hours": round((daily.get("sunshine_duration", [0])[i] or 0) / 3600, 1),
                })
            return results
    except Exception as e:
        logger.error(f"Historical weather fetch failed: {e}")
        return []
