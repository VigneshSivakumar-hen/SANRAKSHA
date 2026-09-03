"""
Satellite-derived soil moisture adapter.

In a real deployment this would call a satellite soil-moisture product
(e.g. ISRO Bhuvan, NASA SMAP) for the given coordinates. Like
imd_service.py, this exposes one stable function and defaults to a
realistic mock so the sync pipeline runs without external network access;
flip USE_MOCK_IMD off and implement `_fetch_real()` against your actual
provider when you have access.
"""

import math
import time

from app.core.config import settings


def _fetch_mock(lat: float, lon: float) -> float:
    seed = int((lat * 1000 + lon * 1000)) % 89
    t = time.time() / 3600
    base = 30 + seed % 35
    wave = 25 * max(0, math.sin(t / 8 + seed * 0.7))
    return round(min(100.0, max(5.0, base + wave)), 1)


def _fetch_real(lat: float, lon: float) -> float:
    raise NotImplementedError(
        "Wire this up to your satellite soil-moisture provider (e.g. ISRO Bhuvan, NASA SMAP)."
    )


def get_latest_soil_moisture(lat: float, lon: float) -> float:
    if settings.USE_MOCK_IMD:
        return _fetch_mock(lat, lon)
    try:
        return _fetch_real(lat, lon)
    except NotImplementedError:
        return _fetch_mock(lat, lon)
