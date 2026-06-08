"""OpenAI Vision integration for lawn disease/weed diagnosis."""

import base64
import json
import logging
import os
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert turfgrass agronomist and lawn care specialist.
Analyze the provided lawn photograph and identify any issues.

For each issue: Name, Type (weed/disease/pest/nutrient/mechanical/other), Severity (low/moderate/severe), Confidence (0-1).
Provide product recommendations with application rates per 1000 sqft and cultural actions.
Consider the user's grass type, location, and weather when making recommendations.

Respond in JSON: {"summary":"...","issues":[{"name":"...","type":"...","severity":"...","confidence":0.85}],"products":[{"name":"...","type":"...","application_rate":"...","timing":"...","notes":"..."}],"actions":[{"action":"...","priority":"immediate|soon|preventive","details":"..."}]}

If lawn looks healthy, say so and suggest preventive maintenance only."""


async def analyze_lawn_photo(
    photo_path: str,
    grass_type: Optional[str] = None,
    location: Optional[str] = None,
    weather_context: Optional[str] = None,
    zone_name: Optional[str] = None,
) -> dict:
    """Analyze a lawn photo using GPT-4o Vision."""
    if not settings.ai_enabled:
        return {
            "summary": "AI diagnosis is not configured. Set OPENAI_API_KEY in your environment to enable.",
            "issues": [], "products": [], "actions": [], "ai_model_used": None,
        }

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        with open(photo_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = os.path.splitext(photo_path)[1].lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        mime_type = mime_map.get(ext, "image/jpeg")

        context_parts = []
        if grass_type: context_parts.append(f"Grass type: {grass_type}")
        if location: context_parts.append(f"Location: {location}")
        if weather_context: context_parts.append(f"Recent weather: {weather_context}")
        if zone_name: context_parts.append(f"Lawn zone: {zone_name}")

        user_message = "Please analyze this lawn photo and identify any issues."
        if context_parts:
            user_message += "\n\nContext:\n" + "\n".join(context_parts)

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}", "detail": "high"}},
                ]},
            ],
            max_tokens=2000, temperature=0.3,
        )

        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        result = json.loads(content.strip())
        result["ai_model_used"] = response.model
        return result

    except Exception as e:
        logger.error(f"AI diagnosis failed: {e}")
        return {"summary": f"AI diagnosis error: {str(e)}", "issues": [], "products": [], "actions": [], "ai_model_used": "error"}
