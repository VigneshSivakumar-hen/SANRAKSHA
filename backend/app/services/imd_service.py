"""
Rainfall data adapter.

Real deployments (USE_MOCK_IMD=false) get rainfall from NASA's POWER API
(see nasa_power_service.py) — public, keyless, and satellite/reanalysis
derived, so it works immediately for any lat/lon without registration.

An optional, secondary path exists for India's own IMD district-rainfall
API if you specifically want IMD as the source and have registered
access — see `_fetch_imd_district()` below. It's off by default because
it needs a per-location `imd_district_id` AND working IMD credentials
that I have not been able to verify from this environment (a request to
a sibling IMD endpoint returned 401 during development, suggesting some
access step isn't publicly documented). Treat it as an unverified
starting point if you want to pursue it.

Both paths fall back to a realistic, gently time-varying mock if they
fail or aren't configured, so the app always has something to show.
"""

import logging
import math
import time
from dataclasses import dataclass

import requests

from app.core.config import settings
from app.services import nasa_power_service

logger = logging.getLogger(__name__)


@dataclass
class RainfallReading:
    rainfall_mm_24h: float
    temperature_c: float
    source: str  # "nasa_power" | "imd" | "imd_mock"


def _fetch_imd_district(district_id: str) -> RainfallReading:
    """Unverified secondary path — see module docstring."""
    resp = requests.get(
        f"{settings.IMD_API_BASE_URL}/districtrainfall",
        params={"id": district_id, "api_key": settings.IMD_API_KEY} if settings.IMD_API_KEY else {"id": district_id},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    rainfall = data.get("rainfall_mm_24h", data.get("rainfall"))
    if rainfall is None:
        raise ValueError(f"Unrecognized IMD response shape: {data!r}")
    return RainfallReading(
        rainfall_mm_24h=float(rainfall),
        temperature_c=float(data.get("temperature_c", data.get("temperature", 20.0))),
        source="imd",
    )


def _fetch_mock(lat: float, lon: float) -> RainfallReading:
    """Deterministic-but-time-varying mock: a slow sine wave (day/night +
    weather-system drift) plus location-seeded pseudo-randomness, so
    repeated calls for the same location move gradually instead of
    jumping around, and different locations look different from each
    other."""
    seed = int((lat * 1000 + lon * 1000)) % 97
    t = time.time() / 3600  # hours, monotonic driver for the wave

    base = 15 + seed % 40
    wave = 60 * max(0, math.sin(t / 6 + seed))
    rainfall = round(max(0.0, base + wave), 1)

    temperature = round(22 - (lat - 10) * 0.35 + 3 * math.sin(t / 12 + seed), 1)

    return RainfallReading(rainfall_mm_24h=rainfall, temperature_c=temperature, source="imd_mock")


def get_latest_rainfall(lat: float, lon: float, district_id: str | None = None) -> RainfallReading:
    if settings.USE_MOCK_IMD:
        return _fetch_mock(lat, lon)

    try:
        env = nasa_power_service.fetch(lat, lon)
        return RainfallReading(
            rainfall_mm_24h=env.rainfall_mm_24h, temperature_c=env.temperature_c, source=env.source
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("NASA POWER rainfall fetch failed (%s)", exc)

    if district_id:
        try:
            return _fetch_imd_district(district_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("IMD district rainfall fetch failed (%s)", exc)

    logger.warning("All real rainfall sources failed for (%s, %s); falling back to mock.", lat, lon)
    return _fetch_mock(lat, lon)
