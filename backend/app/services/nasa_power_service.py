"""
NASA POWER API adapter — real environmental data, no API key required.

NASA's POWER project (https://power.larc.nasa.gov) publishes daily
precipitation, soil-wetness, and temperature derived from NASA's MERRA-2
reanalysis, which assimilates satellite observations (this is the same
kind of product agricultural and hydrological applications use — see
e.g. the `nasapower` R package and `pynasapower` Python package, both
built on this exact API). Unlike IMD's district API, POWER is public,
keyless, and works for arbitrary lat/lon worldwide, so this is the
primary real-data path for both imd_service.py (rainfall) and
satellite_service.py (soil moisture) — see USE_MOCK_IMD in each.

Data latency: MERRA-2-based values typically lag by a few days (NASA's
near-real-time processing, not live telemetry), so this fetches a
rolling window and returns the most recent day that has real (non-fill)
data, rather than assuming "today" is available.

Honesty note: this endpoint shape is drawn from NASA's public API
documentation and confirmed by third-party client libraries built on
top of it (nasapower, pynasapower), but this sandbox's network egress
is restricted to a fixed allowlist that does not include
power.larc.nasa.gov, so I have not been able to execute a live test
call against it myself. Verify with a real request once deployed
(Render's outbound network is not restricted the way this sandbox's
is) — e.g. trigger POST /api/sync/run and check the logs / resulting
readings look sane.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

POWER_FILL_VALUE = -999  # NASA's documented sentinel for "no data"
_CACHE_TTL_SECONDS = 3600  # avoid hitting the API twice for the same point
_cache: dict[tuple[float, float], tuple[float, dict]] = {}


@dataclass
class EnvironmentalReading:
    rainfall_mm_24h: float
    soil_moisture_pct: float
    temperature_c: float
    source: str  # "nasa_power" | "mock"


def _round_coord(v: float) -> float:
    # POWER's native grid is ~0.5° x 0.625°; rounding cache keys to 2
    # decimal places is plenty of precision and keeps nearby locations
    # from each triggering their own API call.
    return round(v, 2)


def fetch(lat: float, lon: float) -> EnvironmentalReading:
    """Fetch rainfall + soil moisture + temperature for one point,
    raising on any network/parse failure so callers can decide how to
    fall back."""
    key = (_round_coord(lat), _round_coord(lon))
    cached = _cache.get(key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=10)  # window wide enough to survive NRT latency

    resp = requests.get(
        f"{settings.NASA_POWER_BASE_URL}/temporal/daily/point",
        params={
            "parameters": "PRECTOTCORR,GWETTOP,T2M",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
            "format": "JSON",
        },
        timeout=15,
    )
    resp.raise_for_status()
    payload = resp.json()

    params = payload["properties"]["parameter"]
    rainfall_series = params.get("PRECTOTCORR", {})
    moisture_series = params.get("GWETTOP", {})
    temp_series = params.get("T2M", {})

    # Walk backwards from the most recent day to find the latest one
    # that actually has data (not NASA's -999 fill value).
    reading = None
    for day in sorted(rainfall_series.keys(), reverse=True):
        rainfall = rainfall_series.get(day)
        moisture = moisture_series.get(day)
        temp = temp_series.get(day)
        if rainfall is None or rainfall == POWER_FILL_VALUE:
            continue
        reading = EnvironmentalReading(
            rainfall_mm_24h=max(0.0, float(rainfall)),
            # GWETTOP is a 0-1 wetness fraction; scale to a percentage
            # to match the rest of the app's soil_moisture_pct field.
            soil_moisture_pct=round(min(100.0, max(0.0, float(moisture) * 100)), 1)
            if moisture not in (None, POWER_FILL_VALUE)
            else 50.0,
            temperature_c=float(temp) if temp not in (None, POWER_FILL_VALUE) else 20.0,
            source="nasa_power",
        )
        break

    if reading is None:
        raise ValueError(f"No usable NASA POWER data in the last 10 days for ({lat}, {lon})")

    _cache[key] = (time.time(), reading)
    return reading
