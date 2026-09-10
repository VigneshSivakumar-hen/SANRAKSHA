"""
Satellite-derived soil moisture adapter.

Real deployments (USE_MOCK_IMD=false) get this from NASA's POWER API —
specifically GWETTOP (top-layer soil wetness from NASA's MERRA-2
reanalysis, which assimilates satellite observations). See
nasa_power_service.py for the shared fetch/cache logic — it's the same
underlying call imd_service.py uses for rainfall, so syncing a location
only hits the API once, not twice.

Falls back to a realistic mock on any failure, same as imd_service.py.
"""

import logging
import math
import time

from app.core.config import settings
from app.services import nasa_power_service

logger = logging.getLogger(__name__)


def _fetch_mock(lat: float, lon: float) -> float:
    seed = int((lat * 1000 + lon * 1000)) % 89
    t = time.time() / 3600
    base = 30 + seed % 35
    wave = 25 * max(0, math.sin(t / 8 + seed * 0.7))
    return round(min(100.0, max(5.0, base + wave)), 1)


def get_latest_soil_moisture(lat: float, lon: float) -> float:
    if settings.USE_MOCK_IMD:
        return _fetch_mock(lat, lon)
    try:
        return nasa_power_service.fetch(lat, lon).soil_moisture_pct
    except Exception as exc:  # noqa: BLE001
        logger.warning("NASA POWER soil-moisture fetch failed (%s); falling back to mock.", exc)
        return _fetch_mock(lat, lon)
