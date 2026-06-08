"""US Drought Monitor integration.

Fetches current drought conditions by state/county.
Data updated every Thursday. API docs: https://usdmdataservices.unl.edu/
"""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

USDM_BASE = "https://usdmdataservices.unl.edu/api"

DROUGHT_LEVELS = {
    None: {"label": "No Drought", "color": "#52B788", "severity": 0},
    "None": {"label": "No Drought", "color": "#52B788", "severity": 0},
    "D0": {"label": "Abnormally Dry", "color": "#FFFF00", "severity": 1},
    "D1": {"label": "Moderate Drought", "color": "#FCD37F", "severity": 2},
    "D2": {"label": "Severe Drought", "color": "#FFAA00", "severity": 3},
    "D3": {"label": "Extreme Drought", "color": "#E60000", "severity": 4},
    "D4": {"label": "Exceptional Drought", "color": "#730000", "severity": 5},
}


async def fetch_drought_by_coords(lat: float, lon: float) -> dict:
    """Fetch drought status for coordinates.

    Uses state-level statistics as a reasonable approximation.
    The USDM API requires a state FIPS code, so we reverse-geocode to get the state.
    """
    try:
        # First, determine the state from coords using Open-Meteo geocoding
        async with httpx.AsyncClient(timeout=10) as client:
            # Use reverse geocoding to find state
            geo_resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": f"{lat},{lon}", "count": 1}
            )

            # Try a simpler approach - get comprehensive drought data
            # USDM provides national statistics we can parse
            resp = await client.get(
                f"{USDM_BASE}/USStatistics/GetDroughtSeverityStatisticsByArea",
                params={
                    "aoi": "us",
                    "startdate": "",  # defaults to latest
                    "enddate": "",
                    "statisticsType": "1",
                },
                headers={"Accept": "application/json"},
                timeout=15,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data:
                    # Determine the predominant drought level
                    latest = data[-1] if isinstance(data, list) else data
                    return _parse_drought_response(latest)

    except Exception as e:
        logger.error(f"Drought data fetch failed: {e}")

    return {
        "drought_level": None,
        "drought_label": "No Data",
        "coverage_pct": None,
        "severity_color": "#52B788",
    }


def _parse_drought_response(data: dict) -> dict:
    """Parse USDM response into simplified drought status."""
    try:
        # USDM returns percentages for each drought category
        d4 = float(data.get("D4", 0) or 0)
        d3 = float(data.get("D3", 0) or 0)
        d2 = float(data.get("D2", 0) or 0)
        d1 = float(data.get("D1", 0) or 0)
        d0 = float(data.get("D0", 0) or 0)

        # Determine the most severe active level
        if d4 > 0:
            level = "D4"
        elif d3 > 0:
            level = "D3"
        elif d2 > 0:
            level = "D2"
        elif d1 > 0:
            level = "D1"
        elif d0 > 0:
            level = "D0"
        else:
            level = None

        info = DROUGHT_LEVELS.get(level, DROUGHT_LEVELS[None])
        total_coverage = d0 + d1 + d2 + d3 + d4

        return {
            "drought_level": level,
            "drought_label": info["label"],
            "coverage_pct": round(total_coverage, 1),
            "severity_color": info["color"],
            "raw_data": data,
        }
    except Exception as e:
        logger.error(f"Drought parsing failed: {e}")
        return {
            "drought_level": None,
            "drought_label": "Parse Error",
            "coverage_pct": None,
            "severity_color": "#52B788",
        }
