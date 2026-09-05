"""
IMD (India Meteorological Department) rainfall data adapter.

Real deployments should call the actual IMD API here (set USE_MOCK_IMD=false
and IMD_API_KEY / district IDs in the environment / database). This module
exposes a single stable function, `get_latest_rainfall(lat, lon, district_id)`,
so the rest of the app never has to know whether it's talking to the real
service or the mock.

--- IMPORTANT: read before flipping USE_MOCK_IMD off ---

IMD's district-wise rainfall API (documented at
https://mausam.imd.gov.in/responsive/api_reference.html, endpoint shape
`https://api.imd.gov.in/api/v1/districtrainfall?id=<district_id>`) is what
`_fetch_real()` below targets. Two things to know:

1. It's keyed by IMD's own district ID, not lat/lon. Each Location needs
   its `imd_district_id` set (look yours up from IMD's district map/API
   reference) — locations without one are skipped and fall back to mock.
2. This integration is unverified from this environment: I don't have
   registered IMD API credentials to test against, and a direct request to
   a sibling endpoint returned 401 during development, suggesting some
   endpoints need an access request/token IMD doesn't fully document
   publicly. Treat `_fetch_real()` as a solid starting point, not a proven
   integration — test it with your own credentials, check the response
   shape actually matches `_parse_response()` below, and adjust as needed.

The mock provider returns plausible, gently time-varying rainfall so the
sync loop and dashboard have something realistic to show without any of
the above.
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


def _parse_response(data: dict) -> RainfallReading:
    """Pull rainfall/temperature out of IMD's JSON. Field names are the
    documented shape at time of writing — verify against a live response
    before relying on this, since IMD does not publish a formal schema."""
    rainfall = data.get("rainfall_mm_24h", data.get("rainfall"))
    if rainfall is None:
        raise ValueError(f"Unrecognized IMD response shape: {data!r}")
    return RainfallReading(
        rainfall_mm_24h=float(rainfall),
        temperature_c=float(data.get("temperature_c", data.get("temperature", 20.0))),
        source="imd",
    )


def _fetch_real(district_id: str) -> RainfallReading:
    resp = requests.get(
        f"{settings.IMD_API_BASE_URL}/districtrainfall",
        params={"id": district_id, "api_key": settings.IMD_API_KEY} if settings.IMD_API_KEY else {"id": district_id},
        timeout=10,
    )
    resp.raise_for_status()
    return _parse_response(resp.json())


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

    if not district_id:
        logger.warning(
            "USE_MOCK_IMD is false but this location has no imd_district_id set; "
            "falling back to mock data for it."
        )
        return _fetch_mock(lat, lon)

    try:
        return _fetch_real(district_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("IMD API call failed (%s); falling back to mock data.", exc)
        return _fetch_mock(lat, lon)
