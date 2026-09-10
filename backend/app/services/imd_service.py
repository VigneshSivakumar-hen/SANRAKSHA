"""IMD (India Meteorological Department) rainfall data adapter.

Demo mode is explicit: set USE_MOCK_IMD=true to generate simulated rainfall.
When it is false, this module never substitutes synthetic values for a failed
IMD request. Callers receive DataSourceUnavailable and can retain their last
known reading while reporting the provider as unavailable.
"""

import logging
import math
import time
from dataclasses import dataclass

import requests

from app.core.config import settings
from app.services.source_errors import DataSourceUnavailable

logger = logging.getLogger(__name__)


@dataclass
class RainfallReading:
    rainfall_mm_24h: float
    temperature_c: float
    source: str  # "imd" | "imd_mock"


def _parse_response(data: dict) -> RainfallReading:
    """Pull rainfall/temperature out of IMD's JSON response."""
    rainfall = data.get("rainfall_mm_24h", data.get("rainfall"))
    if rainfall is None:
        raise DataSourceUnavailable(f"Unrecognized IMD response shape: {data!r}")
    return RainfallReading(
        rainfall_mm_24h=float(rainfall),
        temperature_c=float(data.get("temperature_c", data.get("temperature", 20.0))),
        source="imd",
    )


def _fetch_real(district_id: str) -> RainfallReading:
    params = {"id": district_id}
    if settings.IMD_API_KEY:
        params["api_key"] = settings.IMD_API_KEY

    try:
        response = requests.get(
            f"{settings.IMD_API_BASE_URL}/districtrainfall",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return _parse_response(response.json())
    except (requests.RequestException, ValueError) as exc:
        raise DataSourceUnavailable(f"IMD rainfall is unavailable: {exc}") from exc


def _fetch_mock(lat: float, lon: float) -> RainfallReading:
    """Deterministic, time-varying demo rainfall used only in explicit demo mode."""
    seed = int((lat * 1000 + lon * 1000)) % 97
    t = time.time() / 3600
    base = 15 + seed % 40
    wave = 60 * max(0, math.sin(t / 6 + seed))
    rainfall = round(max(0.0, base + wave), 1)
    temperature = round(22 - (lat - 10) * 0.35 + 3 * math.sin(t / 12 + seed), 1)
    return RainfallReading(rainfall_mm_24h=rainfall, temperature_c=temperature, source="imd_mock")


def get_latest_rainfall(lat: float, lon: float, district_id: str | None = None) -> RainfallReading:
    if settings.USE_MOCK_IMD:
        return _fetch_mock(lat, lon)

    if not district_id:
        raise DataSourceUnavailable(
            "IMD rainfall is unavailable because this location has no imd_district_id."
        )

    return _fetch_real(district_id)
