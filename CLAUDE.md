# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Full stack (API + worker + local Postgres)
docker compose --profile local-db up -d

# Without local DB (use external Postgres via DB_HOST in .env)
docker compose up -d

# Rebuild after code changes
docker compose --profile local-db up -d --build

# View logs
docker compose logs -f api
docker compose logs -f worker
```

The app runs at `http://localhost:8080` (configurable via `APP_PORT` in `.env`).

## Database Migrations

Migrations run automatically on container start via `entrypoint.sh`. To run manually (requires DB connectivity):

```bash
cd backend
alembic upgrade head          # apply all migrations
alembic revision --autogenerate -m "description"  # create new migration
```

Migration files live in `backend/alembic/versions/`. The `alembic.ini` hardcodes the default DB URL; for different credentials set `DATABASE_URL` or edit the file. The async `alembic/env.py` imports all models so they register with `Base.metadata` for autogenerate to work.

## Architecture Overview

### Two-process design
- **`api` container**: FastAPI app (`backend/app/main.py`) — serves the REST API and the frontend static files as a single binary.
- **`worker` container**: APScheduler background process (`backend/app/worker/scheduler.py`) — polls weather hourly, generates watering recommendations daily at 6am, and fetches drought status weekly on Thursdays.

Both share the same PostgreSQL database. They do not communicate directly.

### Backend layers
```
app/
  api/        ← FastAPI routers (one file per domain)
  services/   ← Business logic (weather fetch, diagnosis, recommendations, drought)
  models/     ← SQLAlchemy ORM models (extend Base from models/base.py)
  schemas/    ← Pydantic request/response schemas
  config.py   ← All settings from env vars via pydantic-settings
  database.py ← Async SQLAlchemy engine + session factory + get_db() dependency
```

API routes use `get_db()` as a FastAPI dependency for session injection. All DB I/O is async (`asyncpg` driver).

### Frontend
Vanilla JS SPA — no build step, no framework. The FastAPI app serves it directly via `StaticFiles` mounts. The SPA catch-all route in `main.py` returns `index.html` for any unmatched path.

- `frontend/js/app.js` — router (`App.navigate()`) switches pages by calling `PageName.render(el)`.
- `frontend/js/api.js` — single `API` object wrapping all `fetch()` calls to `/api/*`.
- `frontend/js/pages/*.js` — one module per page, each exports a `render(el)` function.
- `frontend/js/components/` — reusable `Modal` and `Toast` components.

### Key external integrations
| Integration | Purpose | Config |
|---|---|---|
| Open-Meteo | Weather + forecast data (free, no key) | None |
| USDM (drought.gov) | US Drought Monitor status | None |
| OpenAI GPT-4o Vision | AI lawn photo diagnosis | `OPENAI_API_KEY` |
| MapTiler | Enhanced satellite map tiles | `MAPTILER_KEY` |

### Startup seeding
On first start, `main.py`'s lifespan creates a default `LawnConfig` row and seeds built-in fertilizer programs (Scotts, Jonathan Green) from `services/fertilizer_catalog.py` if the tables are empty.

### Home Assistant integration
`backend/app/api/homeassistant.py` exposes flat sensor endpoints at `/api/homeassistant/*` designed for HA REST sensors. These return the same data as the main API but in a simplified format for easy `value_template` extraction.

## Environment Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Notes |
|---|---|---|
| `DB_HOST` | `db` | Use `localhost` or external host if not using Docker DB |
| `APP_PORT` | `8080` | Host port mapped to container port 8000 |
| `APP_PIN` | _(empty)_ | Optional PIN lock for the UI |
| `OPENAI_API_KEY` | _(empty)_ | Enables AI diagnosis feature |
| `MAPTILER_KEY` | _(empty)_ | Falls back to Esri satellite if unset |
| `TZ` | `America/New_York` | Affects scheduler timing |
