# Lawny API Reference

Base URL: `http://localhost:8080` (configurable via `APP_PORT`)

All endpoints are under `/api/`. Request and response bodies are JSON unless noted. Errors return `{"detail": "message"}`.

---

## Table of Contents

1. [Dashboard](#dashboard)
2. [Lawn Configuration](#lawn-configuration)
3. [Zones](#zones)
4. [Activities](#activities)
5. [Schedules](#schedules)
6. [Weather](#weather)
7. [AI Diagnosis](#ai-diagnosis)
8. [Soil Tests](#soil-tests)
9. [Observations](#observations)
10. [Product Catalog](#product-catalog)
11. [AI Advisor](#ai-advisor)
12. [Fertilizer Programs](#fertilizer-programs)
13. [Settings](#settings)
14. [Home Assistant](#home-assistant)

---

## Dashboard

### `GET /api/dashboard`

Returns a combined summary used by the dashboard page.

**Response fields:**
- `lawn` — current lawn config (name, grass_type, has_location, ai_provider)
- `avg_health_score` — rolling average health score (float or null)
- `health_trend` — list of `{date, score}` objects
- `days_since_mow` — integer or null
- `upcoming_tasks` — next 5 scheduled items with `days_until`, `is_overdue`
- `recent_activities` — last 10 activities with `type`, `date`, `zone_name`, `notes`

---

## Lawn Configuration

### `GET /api/lawn`
Returns the current lawn config row.

```json
{
  "id": 1,
  "name": "My Lawn",
  "address": "123 Main St",
  "latitude": 40.123,
  "longitude": -74.456,
  "grass_type": "tall_fescue",
  "total_area_sqft": 4500,
  "ai_provider": "openai",
  "usda_zone": "6b"
}
```

### `POST /api/lawn`
Creates the lawn config (first-run only).

### `PUT /api/lawn`
Updates the lawn config.

**Body fields:** `name`, `address`, `latitude`, `longitude`, `grass_type`, `ai_provider`, `usda_zone`

### `POST /api/lawn/geocode`
Geocodes an address string via Nominatim.

**Body:** `{"address": "123 Main St, City, ST"}`

**Response:** `{latitude, longitude, display_name, city, state}`

### `GET /api/lawn/grass-types`
Returns available grass types grouped by season.

```json
{
  "cool_season": [{"value": "tall_fescue", "label": "Tall Fescue"}, ...],
  "warm_season": [{"value": "bermuda", "label": "Bermudagrass"}, ...]
}
```

---

## Zones

### `GET /api/zones`
Returns all lawn zones.

```json
[{"id": 1, "name": "Front Yard", "area_sqft": 2000, "grass_type": "tall_fescue", "shape": {...}}]
```

### `POST /api/zones`
Creates a zone.

**Body:** `name` (required), `area_sqft`, `grass_type`, `shape` (GeoJSON polygon), `notes`

### `PUT /api/zones/{zone_id}`
Updates a zone.

### `DELETE /api/zones/{zone_id}`
Deletes a zone.

---

## Activities

### `GET /api/activities`
Returns logged activities.

**Query params:** `type`, `zone_id`, `limit` (default 100), `offset`

**Response:** list of activity objects with `id`, `date`, `type`, `zone_id`, `zone_name`, `health_score`, `notes`, `data` (JSON)

### `POST /api/activities`
Logs an activity.

**Body:**
```json
{
  "date": "2025-06-01",
  "type": "mow",
  "zone_id": null,
  "health_score": 8,
  "notes": "First cut of the season",
  "data": {}
}
```

**Activity types:** `mow`, `fertilize`, `water`, `weed_control`, `aerate`, `overseed`, `dethatch`, `lime`, `pest_control`, `soil_test`, `observation`, `other`

### `PUT /api/activities/{activity_id}`
Updates an activity.

### `DELETE /api/activities/{activity_id}`
Deletes an activity.

### `GET /api/activities/types`
Returns activity type metadata (icon, label) for all types.

### `GET /api/activities/stats`
Returns aggregate stats: count by type, total mows, days since last mow, average health score.

---

## Schedules

### `GET /api/schedules`
Returns all scheduled tasks.

### `POST /api/schedules`
Creates a schedule.

**Body:** `type` (required), `due_date` (required), `zone_id`, `recurrence`, `notes`

### `PUT /api/schedules/{schedule_id}`
Updates a schedule.

### `DELETE /api/schedules/{schedule_id}`
Deletes a schedule.

### `POST /api/schedules/{schedule_id}/complete`
Marks a schedule item complete and advances the next occurrence for recurring items.

### `GET /api/schedules/upcoming`
Returns upcoming tasks within a window.

**Query params:** `days` (default 14)

**Response:** list with `days_until`, `is_overdue`, `type`, `due_date`, `zone_name`

---

## Weather

All weather endpoints require a lawn location (lat/lon) to be configured.

### `GET /api/weather/current`
Current conditions from Open-Meteo.

```json
{
  "temperature_f": 72.4,
  "weather_code": 1,
  "weather_description": "Mainly clear",
  "humidity_pct": 58,
  "uv_index": 5.2,
  "soil_temp_surface_f": 68.1,
  "wind_speed_mph": 7.3,
  "precipitation_in": 0.0
}
```

### `GET /api/weather/forecast`
**Query params:** `days` (default 7, max 14)

Returns daily forecast with `date`, `temp_high_f`, `temp_low_f`, `precipitation_in`, `precipitation_probability`, `uv_index_max`.

### `GET /api/weather/history`
**Query params:** `days` (default 30)

Returns historical daily weather with `rain_in`, `temp_high_f`, `temp_low_f`.

### `GET /api/weather/drought`
Current US Drought Monitor status for the lawn's location.

```json
{
  "drought_level": "D1",
  "drought_label": "Moderate Drought",
  "severity": 1,
  "color": "#FFFF00",
  "coverage_pct": 45
}
```

Returns `{"drought_level": "None"}` when no drought is active.

### `GET /api/weather/watering`
AI-generated watering recommendation.

```json
{
  "recommendation": "light",
  "frequency": "Every 2-3 days",
  "duration_minutes": 20,
  "reasoning": "..."
}
```

`recommendation` values: `none`, `light`, `moderate`, `heavy`

### `GET /api/weather/hydration-balance`
Comprehensive 14-day hydration analysis.

**Response fields:**
- `balance` — `{past_delta_in, projected_delta_in, status_label}`
- `past` — `{rain_in, watering_logged_in, total_received_in, total_need_in, daily[...]}`
- `future` — `{predicted_rain_in, predicted_need_in, daily[...]}`
- `weekly_need_in` — target weekly inches
- `drought` — current drought object
- `adjustments` — `{explanation, multiplier}`

---

## AI Diagnosis

Requires at least one AI provider configured.

### `POST /api/diagnosis/analyze`
Analyzes a lawn photo. `multipart/form-data`.

**Form fields:**
- `photo` (file, required) — image file
- `zone_id` (int, optional) — zone context
- `ai_provider` (string, optional) — override provider: `openai`, `anthropic`, `gemini`

**Response:**
```json
{
  "id": 12,
  "summary": "Lawn shows signs of brown patch disease...",
  "issues": [
    {"name": "Brown Patch", "type": "disease", "severity": "moderate", "confidence": 0.87}
  ],
  "products": [
    {"name": "Scotts DiseaseEx", "application_rate": "2 lbs/1000 sqft", "timing": "Immediately", "notes": "..."}
  ],
  "actions": [
    {"priority": "immediate", "action": "Apply fungicide", "details": "..."}
  ],
  "ai_provider": "openai",
  "ai_model": "gpt-4o",
  "created_at": "2025-06-01T10:00:00Z"
}
```

### `GET /api/diagnosis/history`
**Query params:** `limit` (default 20)

Returns list of past diagnoses with `id`, `summary`, `issue_count`, `photo_url`, `created_at`.

### `GET /api/diagnosis/{diagnosis_id}`
Returns a single diagnosis with full details.

---

## Soil Tests

### `GET /api/soil-tests`
Returns all soil tests, newest first.

**Query params:** `zone_id`, `limit` (default 50)

**Response:** list of soil test objects (see fields below).

### `POST /api/soil-tests`
Logs a new soil test.

**Body:**
```json
{
  "test_date": "2025-05-15",
  "zone_id": null,
  "lab_name": "UMass Extension",
  "ph": 6.2,
  "buffer_ph": 6.8,
  "nitrogen_ppm": 12,
  "phosphorus_ppm": 45,
  "potassium_ppm": 180,
  "calcium_ppm": 1200,
  "magnesium_ppm": 180,
  "sulfur_ppm": 10,
  "organic_matter_pct": 3.8,
  "cec": 12.5,
  "lime_recommendation_lbs_per_1k": 50,
  "notes": "Front yard test"
}
```

All nutrient fields are optional — log only what you have.

### `GET /api/soil-tests/latest`
Returns the most recent soil test, augmented with a full interpretation.

**Response includes `interpretation` object:**
```json
{
  "interpretation": {
    "ph_status": {"status": "low", "label": "Acidic", "color": "warning", "action": "Apply lime..."},
    "nutrients": {
      "phosphorus_ppm": {"status": "optimal", "label": "Optimal", "color": "success"},
      "potassium_ppm": {"status": "low", "label": "Low", "color": "warning"}
    },
    "amendments": [
      {"type": "lime", "amount_lbs_total": 250, "amount_lbs_per_1k": 50, "product": "Pelletized Lime"}
    ],
    "overall_score": 72,
    "summary": ["Soil pH is acidic at 6.2 — apply lime", "Potassium is low — use a K-rich fertilizer"]
  }
}
```

### `GET /api/soil-tests/{test_id}`
Returns a single soil test with interpretation.

### `PUT /api/soil-tests/{test_id}`
Updates a soil test. Same body fields as POST.

### `DELETE /api/soil-tests/{test_id}`
Deletes a soil test.

### `POST /api/soil-tests/calculate-amendment`
Calculates lime or sulfur amendment without saving a test.

**Body:**
```json
{
  "current_ph": 5.8,
  "target_ph": 6.5,
  "area_sqft": 4000,
  "soil_type": "loam",
  "buffer_ph": 6.6,
  "amendment_type": "lime"
}
```

`soil_type` options: `sandy`, `loam`, `clay`  
`amendment_type` options: `lime`, `sulfur`

**Response:**
```json
{
  "needed": true,
  "amount_lbs_per_1000sqft": 50,
  "amount_lbs_total": 200,
  "product_suggestion": "Pelletized Dolomitic Lime",
  "notes": "Apply in fall for best results...",
  "method": "Penn State buffer pH"
}
```

---

## Observations

### `GET /api/observations/types`
Returns all observation type metadata.

```json
[
  {"value": "weed_pressure", "label": "General Weeds", "icon": "🌿"},
  {"value": "brown_patch", "label": "Brown Patch", "icon": "🟤"},
  ...
]
```

**All types:** `weed_pressure`, `clover`, `moss`, `crabgrass`, `nutsedge`, `dandelion`, `bare_spots`, `brown_patch`, `dollar_spot`, `grub_damage`, `thatch`, `compaction`, `insect`, `fungus`, `discoloration`, `other`

### `GET /api/observations`
Returns observations, newest first.

**Query params:** `status` (`active`, `monitoring`, `resolved`), `zone_id`, `observation_type`, `limit`

**Response:** list with `id`, `observation_type`, `type_label`, `type_icon`, `severity`, `coverage_pct`, `zone_id`, `zone_name`, `description`, `photo_url`, `status`, `date`, `resolved_date`, `created_at`

### `POST /api/observations`
Logs an observation.

**Body:**
```json
{
  "observation_type": "crabgrass",
  "severity": "moderate",
  "coverage_pct": 15,
  "zone_id": 2,
  "date": "2025-06-01",
  "description": "Coming up along the driveway edge"
}
```

`severity` values: `low`, `moderate`, `severe`

### `POST /api/observations/with-photo`
Logs an observation with a photo. `multipart/form-data`.

**Form fields:** `observation_type`, `severity`, `coverage_pct`, `zone_id`, `description`, `photo` (file)

### `GET /api/observations/{obs_id}`
Returns a single observation.

### `PUT /api/observations/{obs_id}`
Updates an observation.

### `POST /api/observations/{obs_id}/resolve`
Marks an observation resolved.

**Body:** `{"resolution_notes": "Applied Drive XLR8, cleared within 3 weeks"}`

### `DELETE /api/observations/{obs_id}`
Deletes an observation.

---

## Product Catalog

A catalog of 40+ built-in lawn care products (fertilizers, pre/post-emergents, herbicides, fungicides, insecticides, soil amendments, seeds) plus user-added custom products.

### `GET /api/products/categories`
Returns all product categories.

```json
[
  {"value": "fertilizer", "label": "Fertilizer"},
  {"value": "pre_emergent", "label": "Pre-Emergent"},
  {"value": "post_emergent", "label": "Post-Emergent"},
  {"value": "herbicide", "label": "Herbicide"},
  {"value": "fungicide", "label": "Fungicide"},
  {"value": "insecticide", "label": "Insecticide"},
  {"value": "soil_amendment", "label": "Soil Amendment"},
  {"value": "seed", "label": "Seed"},
  {"value": "other", "label": "Other"}
]
```

### `GET /api/products`
Returns products.

**Query params:** `category`, `brand`, `q` (search term), `limit` (default 100)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Scotts Turf Builder Weed & Feed",
    "brand": "Scotts",
    "category": "fertilizer",
    "npk": "28-0-3",
    "description": "Fertilizer + broadleaf weed control",
    "application_rate": "2.5 lbs / 1000 sqft",
    "application_timing": "Spring, when weeds are actively growing",
    "is_builtin": true
  }
]
```

### `GET /api/products/{product_id}`
Returns a single product.

### `POST /api/products`
Adds a custom product.

**Body:** `name` (required), `brand`, `category`, `npk`, `description`, `application_rate`, `application_timing`, `price`, `where_to_buy`, `notes`

### `PUT /api/products/{product_id}`
Updates a custom product (built-in products cannot be edited).

### `DELETE /api/products/{product_id}`
Deletes a custom product (built-in products cannot be deleted).

---

## AI Advisor

Requires at least one AI provider configured. See `GET /api/ai/providers` to check what is available.

### `POST /api/ai/consult`
Submits a lawn care question to the AI. The backend assembles a full context bundle (soil test, active observations, recent activities, current weather, seasonal alerts) before calling the AI.

**Body:**
```json
{
  "question": "I'm seeing clover spreading across my front yard — how do I get rid of it?",
  "observation_ids": [3, 7],
  "zone_id": 1
}
```

`observation_ids` and `zone_id` are optional. When provided, the context bundle focuses on those observations/zone.

**Response:**
```json
{
  "id": 5,
  "question": "I'm seeing clover spreading...",
  "summary": "Clover is typically a sign of low nitrogen...",
  "root_cause": "Nitrogen deficiency allows clover to outcompete grass",
  "immediate_actions": [
    {
      "priority": "soon",
      "action": "Apply a broadleaf herbicide containing triclopyr",
      "details": "Target when temps are 60-85°F and no rain for 24 hours"
    }
  ],
  "products": [
    {
      "name": "Ortho WeedClear",
      "category": "herbicide",
      "application_rate": "As directed on label",
      "timing": "Spring or fall",
      "notes": "Safe for most grass types"
    }
  ],
  "prevention": "Maintain nitrogen levels with regular fertilization — clover cannot compete with dense, well-fed turf",
  "expected_timeline": "2-3 weeks for clover to die back after treatment",
  "watch_for": "Re-emergence in late summer if nitrogen remains low",
  "ai_provider": "openai",
  "ai_model": "gpt-4o",
  "created_at": "2025-06-01T10:00:00Z"
}
```

`priority` values: `immediate`, `soon`, `later`

### `GET /api/ai/consultations`
Returns past consultations.

**Query params:** `limit` (default 20)

**Response:** list with `id`, `question`, `summary`, `ai_provider`, `created_at`

### `GET /api/ai/consultations/{consult_id}`
Returns a single consultation with full structured response.

### `GET /api/ai/seasonal-alerts`
Returns active seasonal alerts for the current month and lawn location, filtered by grass type.

**Response:**
```json
[
  {
    "id": "japanese_beetle",
    "name": "Japanese Beetle",
    "type": "pest",
    "severity": "high",
    "icon": "🪲",
    "title": "Japanese Beetle Season",
    "description": "Adults emerge in June-July and skeletonize grass blades...",
    "risk_conditions": "Warm summers following wet spring",
    "preventive_action": "Apply grub preventive (imidacloprid) in late spring",
    "curative_action": "Spray adult beetles with pyrethrin; apply Dylox for grubs",
    "products": ["GrubEx", "Dylox"],
    "watch_for": "C-shaped white grubs 1-2 inches below surface"
  }
]
```

`severity` values: `low`, `medium`, `high`, `critical`  
`type` values: `pest`, `disease`, `weed`, `cultural`

### `GET /api/ai/providers`
Returns which AI providers are configured and their active models.

```json
{
  "openai":     {"enabled": true,  "model": "gpt-4o"},
  "anthropic":  {"enabled": false, "model": "claude-sonnet-4-6"},
  "gemini":     {"enabled": false, "model": "gemini-2.0-flash"}
}
```

---

## Fertilizer Programs

### `GET /api/fertilizer/programs`
Returns all available programs (built-in + custom).

### `GET /api/fertilizer/programs/{program_id}`
Returns a program with all steps.

**Response:**
```json
{
  "id": 1,
  "name": "4-Step Program",
  "brand": "Scotts",
  "grass_types": ["tall_fescue", "kentucky_bluegrass"],
  "steps": [
    {
      "id": 1,
      "step_number": 1,
      "product_name": "Turf Builder with Halts",
      "season": "early_spring",
      "month_label": "March-April",
      "icon_emoji": "🌱",
      "status": "current",
      "applied_date": null
    }
  ]
}
```

`step.status` values: `upcoming`, `current`, `overdue`, `done`

### `POST /api/fertilizer/programs/refresh`
Re-seeds built-in programs from the catalog (destructive — only use to reset).

### `POST /api/fertilizer/programs/custom`
Creates a custom program.

**Body:** `name` (required), `brand`, `description`, `grass_types` (list)

### `PUT /api/fertilizer/programs/custom/{program_id}`
Updates a custom program header.

### `DELETE /api/fertilizer/programs/custom/{program_id}`
Deletes a custom program.

### `POST /api/fertilizer/programs/custom/{program_id}/steps`
Adds a step to a custom program.

**Body:** `step_number`, `product_name` (required), `season`, `month_label`, `timing_notes`, `application_rate`, `icon_emoji`

### `PUT /api/fertilizer/programs/custom/{program_id}/steps/{step_id}`
Updates a step.

### `DELETE /api/fertilizer/programs/custom/{program_id}/steps/{step_id}`
Deletes a step.

### `GET /api/fertilizer/active`
Returns the active program with current progress, or `null` if none active.

```json
{
  "program": {"id": 1, "name": "4-Step Program", "brand": "Scotts"},
  "steps": [...],
  "completed": 2,
  "total": 4,
  "progress_pct": 50
}
```

### `POST /api/fertilizer/active`
Activates a program.

**Body:** `{"program_id": 1}`

### `DELETE /api/fertilizer/active`
Deactivates the current program (does not delete it).

### `POST /api/fertilizer/apply/{step_id}`
Marks a step applied and logs an activity.

**Body:** `{"date": "2025-04-10", "notes": "Applied at 50 lbs", "health_score": 7}`

### `GET /api/fertilizer/shopping-list`
Returns products needed for the active program's remaining steps.

---

## Settings

### `GET /api/settings`
Returns current settings with integration status.

```json
{
  "lawn": {
    "name": "My Lawn",
    "grass_type": "tall_fescue",
    "latitude": 40.123,
    "longitude": -74.456,
    "ai_provider": "openai"
  },
  "integrations": {
    "weather": true,
    "drought": true,
    "ai_diagnosis": true,
    "maptiler": false
  }
}
```

### `PUT /api/settings/ai-provider`
Sets the active AI provider.

**Body:** `{"ai_provider": "anthropic"}`

Returns `400` if the provider is not configured (no API key set).

### `GET /api/settings/pin-check`
Returns `{"pin_required": true/false}`.

### `POST /api/settings/pin-verify`
**Body:** `{"pin": "1234"}`

Returns `{"valid": true/false}`.

---

## Home Assistant

Flat endpoints designed for HA REST sensor integration. All values are primitives for easy `value_template` extraction.

### `GET /api/homeassistant/states`
All sensor data in one response.

**Key fields:**
```
temperature_f, soil_temp_f, humidity_pct, uv_index
weather_code, weather_description
watering_recommendation, watering_frequency, watering_duration_minutes
weekly_need_inches, weekly_rain_inches, weekly_watered_inches
hydration_status, hydration_delta_inches
drought_level, drought_label, drought_severity
health_score, days_since_mow
fertilizer_program, fertilizer_progress_pct, fertilizer_next_step
```

### `GET /api/homeassistant/watering`
Detailed 14-day per-day breakdown with `date`, `rain_in`, `need_in`, `watered_in`.

### `GET /api/homeassistant/fertilizer`
Current fertilizer program name, progress percentage, next step details.

### `GET /api/homeassistant/activities`
**Query params:** `limit` (default 10)

Returns recent activities in a flat format.

---

## Changelog

### v2.0.0

**New endpoints:**
- `/api/soil-tests` — full CRUD + soil interpretation + amendment calculator
- `/api/observations` — observation logging with 16 types, severity, coverage, status workflow
- `/api/products` — product catalog with 40+ built-in products across 9 categories
- `/api/ai/consult` — full-context AI consultation with structured JSON response
- `/api/ai/consultations` — consultation history
- `/api/ai/seasonal-alerts` — geo-aware, month-filtered seasonal pest/disease alerts
- `/api/ai/providers` — which AI providers are configured
- `/api/settings/ai-provider` — switch active AI provider

**Modified endpoints:**
- `POST /api/diagnosis/analyze` — accepts optional `ai_provider` field to override provider per-request
- `GET /api/settings` — response now includes `lawn.ai_provider`
- `PUT /api/lawn` — accepts `ai_provider` and `usda_zone` fields

**New AI providers:**
- `anthropic` — Anthropic Claude (claude-sonnet-4-6), enabled via `ANTHROPIC_API_KEY`
- `gemini` — Google Gemini (gemini-2.0-flash), enabled via `GEMINI_API_KEY`
- `openai` — OpenAI GPT-4o (existing), enabled via `OPENAI_API_KEY`
