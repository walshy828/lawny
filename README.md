# 🌿 Lawny

**Lawny** is a self-hosted, smart lawn care manager that combines weather intelligence, AI-powered diagnostics, soil science, and proactive seasonal guidance to help you grow a healthier lawn.

## Features

### 💧 Water Intelligence
- **Hydration Balance** — Compare actual water (rain + logged irrigation) against ET-based need with a 14-day stacked timeline
- **Smart Watering Plans** — Recommendations that adjust for soil temperature, humidity, and forecasted precipitation
- **Drought Monitor** — Real-time USDM integration with severity badges and pulse animations for active drought conditions

### 🤖 Multi-Provider AI
- **Photo Diagnosis** — Upload photos of problem areas; AI identifies weeds, diseases, and pests with treatment plans
- **AI Advisor** — Ask any lawn care question using the full context of your soil tests, weather, observations, and activities
- **Provider Choice** — Connect OpenAI GPT-4o, Anthropic Claude, or Google Gemini — switch providers from Settings
- **What-If Scenarios** — Select an observation type and severity, then get structured root cause, actions, products, and prevention advice

### 🧪 Soil Test Tracking
- **Log test results** — pH, N/P/K, calcium, magnesium, sulfur, organic matter, CEC
- **Interpretation engine** — Auto-classifies each nutrient as deficient / optimal / excessive with color coding
- **Amendment calculator** — Lime and sulfur dosing using Penn State buffer pH method, adjusted for soil type and zone area
- **Trend over time** — All tests are timestamped; the dashboard shows the latest reading at a glance

### 👁️ Observation Logging
- **16 observation types** — Weeds, clover, moss, bare spots, fungus, grub damage, thatch, discoloration, and more
- **Severity + coverage** — Track how bad an issue is and how much of the lawn it covers
- **Status workflow** — Active → Monitoring → Resolved with resolution notes
- **Direct AI path** — "Ask AI" on any observation pre-fills the AI Advisor with full context

### 🌿 Fertilizer Management
- **Brand programs** — Scotts, Jonathan Green, and other major programs with step-by-step schedules
- **Custom programs** — Build your own application calendar with any product and timing
- **Progress tracking** — Visual progress bar and overdue alerts on the dashboard

### 🗺️ Lawn Mapping & Zones
- Draw and manage zones on a satellite map (MapTiler or Esri fallback)
- Per-zone square footage drives product amount calculations

### 📡 Seasonal Alerts
- 21 geo-aware alerts (Japanese beetles, fire ants, brown patch, crabgrass, etc.)
- Filtered by your lawn's coordinates, current month, and grass type
- Displayed on the dashboard with preventive action summaries

### 🏠 Home Assistant Integration
Flat sensor endpoints designed for HA REST sensors — no templating gymnastics required.

```yaml
rest:
  - resource: http://YOUR_LAWNY_IP:8080/api/homeassistant/states
    scan_interval: 300
    sensor:
      - name: "Lawn Watering Recommendation"
        value_template: "{{ value_json.watering_recommendation }}"
      - name: "Lawn Soil Temp"
        value_template: "{{ value_json.soil_temp_f }}"
        unit_of_measurement: "°F"
      - name: "Lawn Health Score"
        value_template: "{{ value_json.health_score }}"
      - name: "Lawn Fertilizer Progress"
        value_template: "{{ value_json.fertilizer_progress_pct }}"
        unit_of_measurement: "%"
```

---

## Getting Started

### Requirements
- Docker and Docker Compose
- At least one AI API key (optional, enables AI features):
  - OpenAI: `OPENAI_API_KEY`
  - Anthropic Claude: `ANTHROPIC_API_KEY`
  - Google Gemini: `GEMINI_API_KEY`
- MapTiler API key (optional — falls back to free Esri tiles)

### Setup

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Edit .env — add API keys, set APP_PORT if needed

# 3. Start with local Postgres
docker compose --profile local-db up -d

# 4. Open the app
open http://localhost:8080
```

After first launch, open **Settings** to set your lawn address and grass type. Draw zones in the **Map** tab to enable area-based product calculations.

### Rebuild after code changes

```bash
docker compose --profile local-db up -d --build
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `db` | Postgres host (`localhost` for external DB) |
| `APP_PORT` | `8080` | Host port |
| `TZ` | `America/New_York` | Affects scheduler timing |
| `APP_PIN` | _(empty)_ | Optional PIN to lock the UI |
| `OPENAI_API_KEY` | _(empty)_ | GPT-4o for photo diagnosis and consultation |
| `ANTHROPIC_API_KEY` | _(empty)_ | Claude for consultation |
| `GEMINI_API_KEY` | _(empty)_ | Gemini for consultation |
| `MAPTILER_KEY` | _(empty)_ | Enhanced satellite tiles; falls back to Esri |

---

## Architecture

Two containers share one Postgres database:

- **`api`** — FastAPI serving the REST API and the frontend SPA as static files
- **`worker`** — APScheduler running background jobs: hourly weather sync, daily watering recommendations, weekly drought status, weekly seasonal alert logging

The frontend is a vanilla JS SPA (no build step). Routes are switched client-side by `App.navigate()`; each page module exports a `render(el)` function.

See `CLAUDE.md` for full architecture details and development commands.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy (async), Alembic |
| Frontend | Vanilla JS, CSS variables, Leaflet.js |
| Database | PostgreSQL (asyncpg driver) |
| AI | OpenAI GPT-4o · Anthropic Claude · Google Gemini |
| Weather | Open-Meteo (free, no key) |
| Drought | US Drought Monitor (USDM) |
| Maps | MapTiler / Esri World Imagery |

---

## License

MIT License.
