"""Multi-provider AI service — OpenAI, Anthropic Claude, and Google Gemini.

API keys are resolved in priority order: DB-stored key → environment variable.
Pass db_config=db_config_from_lawn(lawn) to get_provider() to use DB keys.
"""

import base64
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# ── Fallback model lists (shown when API key is not yet configured) ───────────
# These are updated manually when new models release; the live list comes from
# each provider's models API once a key is saved.
AVAILABLE_MODELS = {
    "openai": [
        {"id": "gpt-4o", "label": "GPT-4o"},
        {"id": "gpt-4o-mini", "label": "GPT-4o Mini"},
        {"id": "o1", "label": "o1"},
        {"id": "o3", "label": "o3"},
        {"id": "o3-mini", "label": "o3 Mini"},
        {"id": "o4-mini", "label": "o4 Mini"},
    ],
    "anthropic": [
        {"id": "claude-opus-4-8", "label": "Claude Opus 4.8"},
        {"id": "claude-sonnet-4-6", "label": "Claude Sonnet 4.6"},
        {"id": "claude-haiku-4-5", "label": "Claude Haiku 4.5"},
    ],
    "gemini": [
        {"id": "gemini-2.5-pro", "label": "Gemini 2.5 Pro"},
        {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
        {"id": "gemini-2.0-flash", "label": "Gemini 2.0 Flash"},
        {"id": "gemini-1.5-pro", "label": "Gemini 1.5 Pro"},
    ],
}

DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-6",
    "gemini": "gemini-2.5-flash",
}


def _format_openai_label(model_id: str) -> str:
    """Turn 'gpt-4o-mini-2024-07-18' → 'GPT-4o Mini (2024-07-18)'."""
    date_match = re.search(r'(-\d{4}-\d{2}-\d{2})$', model_id)
    date_suffix = f" ({date_match.group(1)[1:]})" if date_match else ""
    base = re.sub(r'-\d{4}-\d{2}-\d{2}$', '', model_id)
    label = base.replace("gpt-", "GPT-").replace("-turbo", " Turbo").replace("-mini", " Mini")
    label = re.sub(r'-(\d)', r' \1', label)  # gpt-4.1 → GPT-4.1
    return label.strip() + date_suffix

# ── System prompts ────────────────────────────────────────────────────────────
DIAGNOSIS_SYSTEM_PROMPT = """You are an expert turfgrass agronomist and lawn care specialist.
Analyze the provided lawn photograph and identify any issues.

For each issue: Name, Type (weed/disease/pest/nutrient/mechanical/other), Severity (low/moderate/severe), Confidence (0-1).
Provide product recommendations with application rates per 1000 sqft and cultural actions.
Consider the user's grass type, location, and weather when making recommendations.

Respond ONLY in valid JSON:
{"summary":"...","issues":[{"name":"...","type":"...","severity":"...","confidence":0.85}],"products":[{"name":"...","type":"...","application_rate":"...","timing":"...","notes":"..."}],"actions":[{"action":"...","priority":"immediate|soon|preventive","details":"..."}]}

If lawn looks healthy, say so and suggest preventive maintenance only."""

CONSULT_SYSTEM_PROMPT = """You are an expert turfgrass agronomist and lawn care consultant.
You have deep knowledge of cool-season and warm-season grasses, soil science, fertilizers, herbicides, fungicides, and integrated pest management.
The user will provide context about their lawn (grass type, location, soil tests, current observations, recent activities, weather) and ask a question.

Provide practical, specific, and actionable advice. Include:
1. Root cause analysis
2. Immediate remediation steps
3. Long-term prevention strategy
4. Specific product recommendations with timing and application rates
5. What to watch for and when to expect results

Respond in this JSON format:
{
  "summary": "...",
  "root_cause": "...",
  "immediate_actions": [{"action": "...", "priority": "immediate|soon|preventive", "details": "..."}],
  "products": [{"name": "...", "category": "...", "application_rate": "...", "timing": "...", "notes": "..."}],
  "prevention": "...",
  "expected_timeline": "...",
  "watch_for": "..."
}"""

ASSESSMENT_SYSTEM_PROMPT = """You are an expert turfgrass agronomist creating a comprehensive lawn remediation plan.
The user has walked their entire lawn and catalogued every problem they found. Your job is to analyze ALL findings together
and produce a coordinated, conflict-free action plan — because lawn treatments interact (you cannot overseed and apply
pre-emergent in the same window; some herbicides harm overseeded areas, etc.).

Given the lawn's grass type, location/region, current month, soil data, and weather, produce a prioritized plan with:
1. Actions ordered by urgency and treatment dependencies (what must happen before what)
2. Specific timing windows using the exact calendar month number when the action should be performed
3. Products with application rates and where to buy
4. Explicit conflict warnings (e.g., "Do not overseed until pre-emergent clears in October")
5. Expected outcomes per problem with realistic timelines

Respond ONLY in valid JSON:
{
  "findings_summary": "Brief paragraph describing the overall lawn condition and the key issues identified",
  "seasonal_context": "What this time of year means for the identified problems and treatment windows",
  "action_steps": [
    {
      "order": 1,
      "priority": "critical|high|medium|low",
      "schedule_month": 6,
      "schedule_week": 1,
      "week_target": "human-readable timing label, e.g. Immediately, Late Spring, Early Fall, Week 1-2",
      "activity_type": "weed_control|fungicide|fertilize|overseed|aerate|lime|pest_control|pre_emergent|post_emergent|dethatch|other",
      "title": "Short action title",
      "description": "What to do and why",
      "product_name": "Specific product name",
      "application_rate": "e.g. 2 lbs per 1000 sqft",
      "timing_notes": "Best time of day, weather conditions needed, etc.",
      "addresses_findings": ["finding_type1", "finding_type2"],
      "conflicts_with": ["activity_type that cannot be done same week/month"],
      "must_follow": null
    }
  ],
  "key_warnings": [
    "Do not apply pre-emergent if you plan to overseed before October"
  ],
  "expected_outcomes": [
    {"finding_type": "crabgrass", "expected_resolution": "80% reduction", "timeline": "4-6 weeks"}
  ],
  "integrated_program_notes": "How these remediation steps fit into an annual lawn program"
}

IMPORTANT: schedule_month must be the actual calendar month number (1=January through 12=December) when this action should be performed based on the current month provided in the prompt and the grass type/region. schedule_week is the week of the month (1-4) or null if any time that month is fine.
Order action_steps so earlier steps come first. Flag any step that blocks a later one."""


# ── Helpers ───────────────────────────────────────────────────────────────────
def _encode_image(photo_path: str) -> tuple[str, str]:
    """Return (base64_data, mime_type) for a photo file."""
    with open(photo_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(photo_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    return data, mime_map.get(ext, "image/jpeg")


def _parse_json_response(content: str) -> dict:
    """Extract JSON from AI response, handling markdown code fences."""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    return json.loads(content.strip())


def db_config_from_lawn(lawn) -> dict:
    """Extract AI config dict from a LawnConfig ORM row for use with get_provider()."""
    if not lawn:
        return {}
    return {
        "openai_api_key": getattr(lawn, "openai_api_key", None),
        "openai_model": getattr(lawn, "openai_model", None),
        "anthropic_api_key": getattr(lawn, "anthropic_api_key", None),
        "anthropic_model": getattr(lawn, "anthropic_model", None),
        "gemini_api_key": getattr(lawn, "gemini_api_key", None),
        "gemini_model": getattr(lawn, "gemini_model", None),
    }


def _mask_key(key: Optional[str]) -> Optional[str]:
    """Return masked version of an API key for display (last 4 chars visible)."""
    if not key or len(key) < 8:
        return None
    return f"{'•' * (len(key) - 4)}{key[-4:]}"


# ── Abstract base ─────────────────────────────────────────────────────────────
class AIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    async def analyze_photo(self, photo_path: str, user_message: str) -> dict: ...

    @abstractmethod
    async def consult(self, user_message: str) -> str: ...

    @abstractmethod
    async def analyze_assessment(self, assessment_message: str) -> str: ...


# ── OpenAI ────────────────────────────────────────────────────────────────────
class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._model = model or DEFAULT_MODELS["openai"]

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze_photo(self, photo_path: str, user_message: str) -> dict:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self._api_key)
        img_data, mime_type = _encode_image(photo_path)
        response = await client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_data}", "detail": "high"}},
                ]},
            ],
            max_tokens=2000, temperature=0.3,
        )
        content = response.choices[0].message.content
        result = _parse_json_response(content)
        result["ai_model_used"] = response.model
        return result

    async def consult(self, user_message: str) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self._api_key)
        response = await client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": CONSULT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=2000, temperature=0.3,
        )
        return response.choices[0].message.content

    async def analyze_assessment(self, assessment_message: str) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self._api_key)
        response = await client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": ASSESSMENT_SYSTEM_PROMPT},
                {"role": "user", "content": assessment_message},
            ],
            max_tokens=4000, temperature=0.2,
        )
        return response.choices[0].message.content

    async def list_models(self) -> list[dict]:
        """Fetch available chat models from the OpenAI models API."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
            if resp.status_code != 200:
                return []
            CHAT_PREFIXES = ("gpt-4", "gpt-3.5-turbo", "o1", "o3", "o4")
            EXCLUDE_TERMS = ("instruct", "embedding", "tts", "whisper", "dall", "audio", "realtime", "search")
            seen_bases: set[str] = set()
            models = []
            for m in sorted(resp.json().get("data", []), key=lambda x: x["id"]):
                mid = m["id"]
                if not any(mid.startswith(p) for p in CHAT_PREFIXES):
                    continue
                if any(t in mid for t in EXCLUDE_TERMS):
                    continue
                # Strip date suffix to get base name
                base = re.sub(r'-\d{4}-\d{2}-\d{2}$', '', mid)
                is_dated = base != mid
                label = _format_openai_label(mid)
                models.append({"id": mid, "label": label, "base": base, "dated": is_dated})
                seen_bases.add(base)
            # Put non-dated (alias) entries first, then dated specifics
            models.sort(key=lambda x: (x["dated"], x["id"]))
            return [{"id": m["id"], "label": m["label"]} for m in models]
        except Exception as exc:
            logger.debug(f"OpenAI list_models failed: {exc}")
            return []


# ── Anthropic ─────────────────────────────────────────────────────────────────
class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self._api_key = api_key or settings.ANTHROPIC_API_KEY
        self._model = model or DEFAULT_MODELS["anthropic"]

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze_photo(self, photo_path: str, user_message: str) -> dict:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        img_data, media_type = _encode_image(photo_path)
        response = await client.messages.create(
            model=self._model,
            max_tokens=2000,
            system=DIAGNOSIS_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_data}},
                    {"type": "text", "text": user_message},
                ],
            }],
        )
        content = response.content[0].text
        result = _parse_json_response(content)
        result["ai_model_used"] = response.model
        return result

    async def consult(self, user_message: str) -> str:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        response = await client.messages.create(
            model=self._model,
            max_tokens=2000,
            system=CONSULT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    async def analyze_assessment(self, assessment_message: str) -> str:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        response = await client.messages.create(
            model=self._model,
            max_tokens=4000,
            system=ASSESSMENT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": assessment_message}],
        )
        return response.content[0].text

    async def list_models(self) -> list[dict]:
        """Fetch available models from the Anthropic models API."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
            if resp.status_code != 200:
                return []
            return [
                {"id": m["id"], "label": m.get("display_name", m["id"])}
                for m in resp.json().get("data", [])
            ]
        except Exception as exc:
            logger.debug(f"Anthropic list_models failed: {exc}")
            return []


# ── Gemini ────────────────────────────────────────────────────────────────────
class GeminiProvider(AIProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model or DEFAULT_MODELS["gemini"]

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze_photo(self, photo_path: str, user_message: str) -> dict:
        import google.generativeai as genai
        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(model_name=self._model, system_instruction=DIAGNOSIS_SYSTEM_PROMPT)
        import PIL.Image
        img = PIL.Image.open(photo_path)
        response = await model.generate_content_async([user_message, img])
        result = _parse_json_response(response.text)
        result["ai_model_used"] = self._model
        return result

    async def consult(self, user_message: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(model_name=self._model, system_instruction=CONSULT_SYSTEM_PROMPT)
        response = await model.generate_content_async(user_message)
        return response.text

    async def analyze_assessment(self, assessment_message: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(model_name=self._model, system_instruction=ASSESSMENT_SYSTEM_PROMPT)
        response = await model.generate_content_async(assessment_message)
        return response.text

    async def list_models(self) -> list[dict]:
        """Fetch available Gemini models via the REST API, filtered to text-capable ones."""
        import httpx
        EXCLUDE_TERMS = ("tts", "computer-use", "robotics", "customtools", "-image")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={self._api_key}&pageSize=200",
                )
            if resp.status_code != 200:
                return []
            models = []
            for m in resp.json().get("models", []):
                if "generateContent" not in m.get("supportedGenerationMethods", []):
                    continue
                name = m["name"].replace("models/", "")
                if "gemini" not in name.lower():
                    continue
                if any(t in name.lower() for t in EXCLUDE_TERMS):
                    continue
                display = m.get("displayName", name)
                # Skip models with placeholder display names
                if display.lower().startswith("nano banana"):
                    continue
                models.append({"id": name, "label": display})
            # Sort: higher version numbers first
            models.sort(key=lambda x: x["id"], reverse=True)
            return models
        except Exception as exc:
            logger.debug(f"Gemini list_models failed: {exc}")
            return []


# ── Factory ───────────────────────────────────────────────────────────────────
_PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
}


def get_provider(provider_name: Optional[str] = None, db_config: Optional[dict] = None) -> AIProvider:
    """
    Return the requested AI provider, resolving keys in priority order:
      1. DB-stored key (from db_config dict)
      2. Environment variable
    Falls back to first available provider if the requested one isn't configured.
    """
    cfg = db_config or {}

    def _resolve_key(p: str) -> Optional[str]:
        return cfg.get(f"{p}_api_key") or getattr(settings, f"{p.upper()}_API_KEY", None)

    def _resolve_model(p: str) -> Optional[str]:
        return cfg.get(f"{p}_model") or None

    def _build(p: str) -> Optional[AIProvider]:
        key = _resolve_key(p)
        if key:
            return _PROVIDER_CLASSES[p](api_key=key, model=_resolve_model(p))
        return None

    if provider_name and provider_name in _PROVIDER_CLASSES:
        p = _build(provider_name)
        if p:
            return p

    # Fall back to first available
    for name in ("openai", "anthropic", "gemini"):
        p = _build(name)
        if p:
            return p

    return OpenAIProvider()  # will fail with a clear auth error at call time


def is_provider_enabled(provider_name: str, db_config: Optional[dict] = None) -> bool:
    """Check whether a given provider has a usable API key (DB or env)."""
    cfg = db_config or {}
    key = cfg.get(f"{provider_name}_api_key") or getattr(settings, f"{provider_name.upper()}_API_KEY", None)
    return bool(key)


async def safe_consult(provider: AIProvider, user_message: str) -> tuple[dict, str]:
    """Call consult, parse JSON response. Returns (structured_dict, raw_text)."""
    try:
        raw = await provider.consult(user_message)
        try:
            structured = _parse_json_response(raw)
        except Exception:
            structured = {"summary": raw, "immediate_actions": [], "products": []}
        return structured, raw
    except Exception as e:
        logger.error(f"AI consult failed ({provider.provider_name}): {e}")
        raise
