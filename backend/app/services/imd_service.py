"""
Rainfall data adapter.

Production mode (USE_MOCK_IMD=false) uses real environmental data providers:

1. NASA POWER — primary provider
   - Public and keyless
   - Provides MERRA-2/reanalysis-derived environmental data
   - Works for arbitrary latitude/longitude

2. IMD district rainfall API — optional secondary provider
   - Used when a district_id is available
   - Requires appropriate IMD access/configuration

Mock data is used only when:
    USE_MOCK_IMD=true

or, when a real provider fails:

    ALLOW_MOCK_FALLBACK=true

Production deployments should use:

    USE_MOCK_IMD=false
    ALLOW_MOCK_FALLBACK=false

With mock fallback disabled, real provider failures raise an error
instead of silently presenting simulated environmental data as real data.
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
    """
    Fetch rainfall from the optional IMD district-rainfall endpoint.

    This is a secondary provider. The endpoint requires a valid district
    identifier and may require appropriate IMD API access.
    """

    params = {"id": district_id}

    if settings.IMD_API_KEY:
        params["api_key"] = settings.IMD_API_KEY

    resp = requests.get(
        f"{settings.IMD_API_BASE_URL}/districtrainfall",
        params=params,
        timeout=10,
    )

    resp.raise_for_status()

    data = resp.json()

    rainfall = data.get(
        "rainfall_mm_24h",
        data.get("rainfall"),
    )

    if rainfall is None:
        raise ValueError(
            f"Unrecognized IMD response shape: {data!r}"
        )

    temperature = data.get(
        "temperature_c",
        data.get("temperature", 20.0),
    )

    return RainfallReading(
        rainfall_mm_24h=float(rainfall),
        temperature_c=float(temperature),
        source="imd",
    )


def _fetch_mock(lat: float, lon: float) -> RainfallReading:
    """
    Generate deterministic but time-varying simulated rainfall.

    This function is intended only for local development, demonstrations,
    testing, or explicitly enabled mock fallback operation.
    """

    seed = int((lat * 1000 + lon * 1000)) % 97

    # Hours used as a slowly changing weather-system driver.
    t = time.time() / 3600

    base = 15 + seed % 40

    wave = 60 * max(
        0,
        math.sin(t / 6 + seed),
    )

    rainfall = round(
        max(0.0, base + wave),
        1,
    )

    temperature = round(
        22
        - (lat - 10) * 0.35
        + 3 * math.sin(t / 12 + seed),
        1,
    )

    return RainfallReading(
        rainfall_mm_24h=rainfall,
        temperature_c=temperature,
        source="imd_mock",
    )


def get_latest_rainfall(
    lat: float,
    lon: float,
    district_id: str | None = None,
) -> RainfallReading:
    """
    Return the latest rainfall reading for a location.

    Provider order in production:
        NASA POWER -> IMD district API -> optional mock fallback

    Behavior:

        USE_MOCK_IMD=true
            -> explicit mock mode

        USE_MOCK_IMD=false
            -> attempt real providers

        Real providers fail and ALLOW_MOCK_FALLBACK=true
            -> use mock data

        Real providers fail and ALLOW_MOCK_FALLBACK=false
            -> raise RuntimeError

    The final behavior prevents production from silently displaying
    simulated environmental data.
    """

    # ---------------------------------------------------------
    # Explicit mock mode
    # ---------------------------------------------------------
    if settings.USE_MOCK_IMD:
        logger.info(
            "Using explicitly enabled mock rainfall data for (%s, %s).",
            lat,
            lon,
        )

        return _fetch_mock(lat, lon)

    provider_errors: list[str] = []

    # ---------------------------------------------------------
    # Primary provider: NASA POWER
    # ---------------------------------------------------------
    try:
        env = nasa_power_service.fetch(lat, lon)

        logger.info(
            "Rainfall obtained from NASA POWER for (%s, %s).",
            lat,
            lon,
        )

        return RainfallReading(
            rainfall_mm_24h=env.rainfall_mm_24h,
            temperature_c=env.temperature_c,
            source=env.source,
        )

    except Exception as exc:  # noqa: BLE001
        message = f"NASA POWER: {exc}"
        provider_errors.append(message)

        logger.warning(
            "NASA POWER rainfall fetch failed for (%s, %s): %s",
            lat,
            lon,
            exc,
        )

    # ---------------------------------------------------------
    # Secondary provider: IMD district rainfall
    # ---------------------------------------------------------
    if district_id:
        try:
            reading = _fetch_imd_district(district_id)

            logger.info(
                "Rainfall obtained from IMD for district %s.",
                district_id,
            )

            return reading

        except Exception as exc:  # noqa: BLE001
            message = f"IMD district API: {exc}"
            provider_errors.append(message)

            logger.warning(
                "IMD district rainfall fetch failed for district %s: %s",
                district_id,
                exc,
            )

    # ---------------------------------------------------------
    # Optional mock fallback
    # ---------------------------------------------------------
    if settings.ALLOW_MOCK_FALLBACK:
        logger.warning(
            "All real rainfall providers failed for (%s, %s). "
            "ALLOW_MOCK_FALLBACK=true, so simulated rainfall will be used.",
            lat,
            lon,
        )

        return _fetch_mock(lat, lon)

    # ---------------------------------------------------------
    # Production-safe failure
    # ---------------------------------------------------------
    details = "; ".join(provider_errors)

    logger.error(
        "All real rainfall providers failed for (%s, %s), "
        "and mock fallback is disabled. Errors: %s",
        lat,
        lon,
        details,
    )

    raise RuntimeError(
        f"No real rainfall data available for ({lat}, {lon}). "
        f"Mock fallback is disabled. Provider errors: {details}"
    )