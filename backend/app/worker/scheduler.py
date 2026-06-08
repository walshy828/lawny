"""Background worker — periodic weather polling and recommendation generation."""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import async_session
from app.models import LawnConfig, WeatherSnapshot, WateringRecommendation, DroughtStatus
from app.services.weather import fetch_current_weather, fetch_forecast, fetch_historical_weather
from app.services.drought import fetch_drought_by_coords
from app.services.recommendations import generate_watering_recommendation
from sqlalchemy import select, desc

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger("lawny.worker")


async def get_lawn_location():
    """Get lawn lat/lon from DB."""
    async with async_session() as db:
        result = await db.execute(select(LawnConfig).limit(1))
        lawn = result.scalar_one_or_none()
        if lawn and lawn.latitude and lawn.longitude:
            return lawn.latitude, lawn.longitude, lawn.grass_type
    return None, None, None


async def poll_weather():
    """Fetch and store current weather snapshot."""
    lat, lon, grass = await get_lawn_location()
    if not lat:
        logger.debug("No lawn location configured — skipping weather poll")
        return

    try:
        weather = await fetch_current_weather(lat, lon)
        if not weather:
            return

        async with async_session() as db:
            snapshot = WeatherSnapshot(
                date=datetime.now(),
                temp_high_f=weather.get("temperature_f"),
                temp_low_f=weather.get("temperature_f"),
                soil_temp_0cm_f=weather.get("soil_temp_surface_f"),
                soil_temp_6cm_f=weather.get("soil_temp_6cm_f"),
                precipitation_in=weather.get("precipitation_in"),
                humidity_pct=weather.get("humidity_pct"),
                wind_speed_mph=weather.get("wind_speed_mph"),
                uv_index=weather.get("uv_index"),
                sunshine_hours=weather.get("sunshine_hours"),
                weather_code=weather.get("weather_code"),
                raw_json=weather.get("raw"),
            )
            db.add(snapshot)
            await db.commit()
            logger.info(f"Weather snapshot saved: {weather.get('temperature_f')}°F, soil: {weather.get('soil_temp_surface_f')}°F")

    except Exception as e:
        logger.error(f"Weather poll failed: {e}")


async def generate_daily_recommendation():
    """Generate daily watering recommendation."""
    lat, lon, grass_type = await get_lawn_location()
    if not lat:
        return

    try:
        current = await fetch_current_weather(lat, lon)
        forecast_data = await fetch_forecast(lat, lon, 7)
        historical = await fetch_historical_weather(lat, lon, 7)

        rain_past_7d = sum(d.get("precipitation_in", 0) for d in historical)

        async with async_session() as db:
            drought_result = await db.execute(select(DroughtStatus).order_by(desc(DroughtStatus.date)).limit(1))
            drought = drought_result.scalar_one_or_none()

            rec = generate_watering_recommendation(
                grass_type=grass_type,
                soil_temp_f=current.get("soil_temp_surface_f"),
                rain_past_7d_in=rain_past_7d,
                rain_forecast_7d_in=forecast_data.get("total_precipitation_7d_in", 0),
                current_temp_f=current.get("temperature_f"),
                humidity_pct=current.get("humidity_pct"),
                drought_level=drought.drought_level if drought else None,
            )

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
            await db.commit()
            logger.info(f"Watering recommendation: {rec['recommendation']} — {rec['frequency']}")

    except Exception as e:
        logger.error(f"Daily recommendation failed: {e}")


async def poll_drought():
    """Weekly drought status update."""
    lat, lon, _ = await get_lawn_location()
    if not lat:
        return

    try:
        result = await fetch_drought_by_coords(lat, lon)
        async with async_session() as db:
            ds = DroughtStatus(
                date=datetime.now(),
                drought_level=result.get("drought_level"),
                drought_label=result.get("drought_label", "Unknown"),
                coverage_pct=result.get("coverage_pct"),
                source_data=result.get("raw_data"),
            )
            db.add(ds)
            await db.commit()
            logger.info(f"Drought status: {result.get('drought_label')}")
    except Exception as e:
        logger.error(f"Drought poll failed: {e}")


def main():
    """Start the background scheduler."""
    logger.info("[Lawny Worker] Starting background scheduler...")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(poll_weather, "interval", hours=1, next_run_time=datetime.now())
    scheduler.add_job(generate_daily_recommendation, "cron", hour=6, minute=0)
    scheduler.add_job(poll_drought, "cron", day_of_week="thu", hour=12, minute=0)
    scheduler.start()

    logger.info("[Lawny Worker] Scheduler running — weather hourly, recommendations daily 6am, drought weekly Thu")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("[Lawny Worker] Shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
