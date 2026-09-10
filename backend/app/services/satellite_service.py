"""Satellite-derived soil-moisture adapter.

Simulated soil moisture is available only when USE_MOCK_SATELLITE=true. In
production mode an unimplemented or failing provider raises
DataSourceUnavailable; it is never disguised as a live satellite reading.
"""

import math
import time
from dataclasses import dataclass

from app.core.config import settings
from app.services.source_errors import DataSourceUnavailable


@dataclass
class SoilMoistureReading:
    soil_moisture_pct: float
    source: str  # "satellite" | "satellite_mock"


def _fetch_mock(lat: float, lon: float) -> SoilMoistureReading:
    seed = int((lat * 1000 + lon * 1000)) % 89
    t = time.time() / 3600
    base = 30 + seed % 35
    wave = 25 * max(0, math.sin(t / 8 + seed * 0.7))
    soil_moisture = round(min(100.0, max(5.0, base + wave)), 1)
    return SoilMoistureReading(soil_moisture_pct=soil_moisture, source="satellite_mock")


def _fetch_real(lat: float, lon: float) -> SoilMoistureReading:
    raise DataSourceUnavailable(
        "Satellite soil-moisture provider is not configured. "
        "Connect a verified provider before enabling production satellite mode."
    )


def get_latest_soil_moisture(lat: float, lon: float) -> SoilMoistureReading:
    if settings.USE_MOCK_SATELLITE:
        return _fetch_mock(lat, lon)
    return _fetch_real(lat, lon)
