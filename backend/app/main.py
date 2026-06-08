"""FastAPI application entry point."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.database import async_session
from app.models import LawnConfig
from sqlalchemy import select

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
UPLOAD_DIR = "/app/uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks."""
    async with async_session() as db:
        # Ensure a default lawn config exists
        result = await db.execute(select(LawnConfig).limit(1))
        if not result.scalar_one_or_none():
            db.add(LawnConfig(name="My Lawn"))
            await db.commit()

        # Seed built-in fertilizer programs if table is empty
        from app.models.fertilizer import FertilizerProgram
        fert_result = await db.execute(select(FertilizerProgram).limit(1))
        if not fert_result.scalar_one_or_none():
            from app.services.fertilizer_catalog import seed_builtin_programs
            await seed_builtin_programs(db)

        # Seed product catalog if table is empty
        from app.models.product import ProductCatalog
        prod_result = await db.execute(select(ProductCatalog).limit(1))
        if not prod_result.scalar_one_or_none():
            from app.services.product_catalog import seed_product_catalog
            await seed_product_catalog(db)
    yield


app = FastAPI(title="Lawny", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from app.api.dashboard import router as dashboard_router
from app.api.lawn import router as lawn_router
from app.api.zones import router as zones_router
from app.api.activities import router as activities_router
from app.api.schedule import router as schedule_router
from app.api.weather import router as weather_router
from app.api.diagnosis import router as diagnosis_router
from app.api.settings import router as settings_router
from app.api.fertilizer import router as fertilizer_router
from app.api.homeassistant import router as homeassistant_router
from app.api.soil_tests import router as soil_tests_router
from app.api.observations import router as observations_router
from app.api.products import router as products_router
from app.api.ai_consult import router as ai_consult_router
from app.api.assessments import router as assessments_router
from app.api.program import router as program_router
from app.api.timeline import router as timeline_router

app.include_router(dashboard_router)
app.include_router(lawn_router)
app.include_router(zones_router)
app.include_router(activities_router)
app.include_router(schedule_router)
app.include_router(weather_router)
app.include_router(diagnosis_router)
app.include_router(settings_router)
app.include_router(fertilizer_router)
app.include_router(homeassistant_router)
app.include_router(soil_tests_router)
app.include_router(observations_router)
app.include_router(products_router)
app.include_router(ai_consult_router)
app.include_router(assessments_router)
app.include_router(program_router)
app.include_router(timeline_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "lawny", "version": "2.0.0"}


# Serve uploaded files
if os.path.isdir(UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Serve frontend static files
if os.path.isdir(STATIC_DIR):
    app.mount("/css", StaticFiles(directory=os.path.join(STATIC_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(STATIC_DIR, "js")), name="js")

    @app.get("/manifest.json")
    async def manifest():
        return FileResponse(os.path.join(STATIC_DIR, "manifest.json"))

    # SPA catch-all
    @app.get("/{path:path}")
    async def spa_catchall(path: str):
        file_path = os.path.join(STATIC_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"detail": "Not found"}
