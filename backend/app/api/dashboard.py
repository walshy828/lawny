"""Dashboard API."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.dashboard import get_dashboard_data

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    return await get_dashboard_data(db)
