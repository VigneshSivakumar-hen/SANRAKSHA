"""
IMD (India Meteorological Department) rainfall data adapter.

Real deployments should call the actual IMD / data.gov.in rainfall API here
(set USE_MOCK_IMD=false and IMD_API_KEY in the environment). This module
exposes a single stable function, `get_latest_rainfall(lat, lon)`, so the
rest of the app never has to know whether it's talking to the real service
or the mock — swap the implementation of `_fetch_real()` for your actual
IMD endpoint and nothing else changes.

The mock provider returns plausible, gently time-varying rainfall so the
sync loop and dashboard have something realistic to show without network
access to an external weather API.
"""

import logging
import math
import time
from dataclasses import dataclass

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RainfallReading:
    rainfall_mm_24h: float
    temperature_c: float
    source: str  # "imd" | "imd_mock"


def _fetch_real(lat: float, lon: float) -> RainfallReading:
    """Real IMD API call. Adjust the URL/params/response parsing to match
    whichever IMD or data.gov.in endpoint you have access to — this shape
    (query by lat/lon, read rainfall + temperature out of JSON) is typical
    but the actual field names vary by dataset."""
    resp = requests.get(
        f"{settings.IMD_API_BASE_URL}/rainfall",
        params={"lat": lat, "lon": lon, "api_key": settings.IMD_API_KEY},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return RainfallReading(
        rainfall_mm_24h=float(data["rainfall_mm_24h"]),
        temperature_c=float(data.get("temperature_c", 20.0)),
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


def get_latest_rainfall(lat: float, lon: float) -> RainfallReading:
    if settings.USE_MOCK_IMD:
        return _fetch_mock(lat, lon)
    try:
        return _fetch_real(lat, lon)
    except Exception as exc:  # noqa: BLE001
        logger.warning("IMD API call failed (%s); falling back to mock data.", exc)
        return _fetch_mock(lat, lon)
