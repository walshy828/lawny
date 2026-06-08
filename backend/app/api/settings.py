"""Settings API — lawn config, PIN, AI provider/key management, integration status."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import LawnConfig
from app.config import settings
from app.services.ai_provider import (
    is_provider_enabled, db_config_from_lawn, AVAILABLE_MODELS, DEFAULT_MODELS, _mask_key
)

router = APIRouter(prefix="/api", tags=["settings"])

VALID_AI_PROVIDERS = ["openai", "anthropic", "gemini"]

_SAFE_LAWN_FIELDS = [
    "id", "name", "address", "latitude", "longitude", "grass_type",
    "climate_zone", "ai_provider", "usda_zone",
    "openai_model", "anthropic_model", "gemini_model",
]


def _lawn_safe_dict(lawn: LawnConfig) -> dict:
    """Return lawn config dict with API keys masked, never raw."""
    d = {f: getattr(lawn, f, None) for f in _SAFE_LAWN_FIELDS}
    db_cfg = db_config_from_lawn(lawn)
    # Add masked key info per provider
    for p in VALID_AI_PROVIDERS:
        d[f"{p}_key_configured"] = bool(db_cfg.get(f"{p}_api_key"))
        d[f"{p}_key_masked"] = _mask_key(db_cfg.get(f"{p}_api_key"))
    return d


@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LawnConfig).limit(1))
    lawn = result.scalar_one_or_none()
    db_cfg = db_config_from_lawn(lawn)

    providers = {}
    for p in VALID_AI_PROVIDERS:
        env_key = getattr(settings, f"{p.upper()}_API_KEY", None)
        db_key = db_cfg.get(f"{p}_api_key")
        enabled = is_provider_enabled(p, db_cfg)
        model = db_cfg.get(f"{p}_model") or DEFAULT_MODELS[p]
        providers[p] = {
            "enabled": enabled,
            "model": model,
            "key_source": "database" if db_key else ("environment" if env_key else None),
            "key_masked": _mask_key(db_key or env_key),
            "available_models": AVAILABLE_MODELS[p],
        }

    any_ai = any(v["enabled"] for v in providers.values())

    return {
        "lawn": _lawn_safe_dict(lawn) if lawn else None,
        "integrations": {
            "weather": True,
            "drought": True,
            "ai_diagnosis": any_ai,
            "maptiler": settings.maptiler_enabled,
        },
        "ai_providers": providers,
        "maptiler_key": settings.MAPTILER_KEY or "",
        "pin_enabled": bool(settings.APP_PIN),
    }


@router.put("/settings/ai-config")
async def update_ai_config(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Save API key and/or model for a specific provider to the database.
    Sending api_key="" clears the stored key (falls back to env var).
    """
    provider = data.get("provider")
    if provider not in VALID_AI_PROVIDERS:
        raise HTTPException(400, f"Invalid provider. Must be one of: {VALID_AI_PROVIDERS}")

    result = await db.execute(select(LawnConfig).limit(1))
    lawn = result.scalar_one_or_none()
    if not lawn:
        raise HTTPException(404, "Lawn not configured yet")

    # Update key — empty string = clear (fall back to env)
    if "api_key" in data:
        key_val = data["api_key"].strip() if data["api_key"] else None
        setattr(lawn, f"{provider}_api_key", key_val or None)

    # Update model preference
    if "model" in data and data["model"]:
        valid_models = [m["id"] for m in AVAILABLE_MODELS.get(provider, [])]
        if data["model"] not in valid_models:
            raise HTTPException(400, f"Invalid model for {provider}. Valid: {valid_models}")
        setattr(lawn, f"{provider}_model", data["model"])

    await db.commit()
    await db.refresh(lawn)

    db_cfg = db_config_from_lawn(lawn)
    env_key = getattr(settings, f"{provider.upper()}_API_KEY", None)
    db_key = db_cfg.get(f"{provider}_api_key")
    return {
        "provider": provider,
        "enabled": is_provider_enabled(provider, db_cfg),
        "model": db_cfg.get(f"{provider}_model") or DEFAULT_MODELS[provider],
        "key_source": "database" if db_key else ("environment" if env_key else None),
        "key_masked": _mask_key(db_key or env_key),
        "ok": True,
    }


@router.put("/settings/ai-provider")
async def update_ai_provider(data: dict, db: AsyncSession = Depends(get_db)):
    """Set which provider is used by default."""
    provider = data.get("ai_provider")
    if provider not in VALID_AI_PROVIDERS:
        raise HTTPException(400, f"Invalid ai_provider. Valid: {VALID_AI_PROVIDERS}")

    result = await db.execute(select(LawnConfig).limit(1))
    lawn = result.scalar_one_or_none()
    if not lawn:
        raise HTTPException(404, "Lawn not configured")

    db_cfg = db_config_from_lawn(lawn)
    if not is_provider_enabled(provider, db_cfg):
        raise HTTPException(400, f"{provider} has no API key configured. Add it in Settings → AI Configuration.")

    lawn.ai_provider = provider
    await db.commit()
    return {"ai_provider": lawn.ai_provider, "ok": True}


@router.get("/settings/pin-check")
async def check_pin():
    return {"pin_required": bool(settings.APP_PIN)}


@router.post("/settings/pin-verify")
async def verify_pin(data: dict):
    pin = data.get("pin", "")
    return {"valid": pin == settings.APP_PIN}
