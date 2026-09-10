"""
Soil-moisture environmental data adapter.

Production mode (USE_MOCK_IMD=false) obtains soil wetness from NASA POWER
through the shared nasa_power_service.

NASA POWER's GWETTOP value is derived from NASA's MERRA-2 reanalysis,
which assimilates satellite observations. It is not raw/live satellite
imagery.

Mock data is used only when:

    USE_MOCK_IMD=true

or, after a real provider failure:

    ALLOW_MOCK_FALLBACK=true

Production deployments should use:

    USE_MOCK_IMD=false
    ALLOW_MOCK_FALLBACK=false

With mock fallback disabled, a NASA POWER failure raises an error rather
than silently returning simulated soil-moisture data.
"""

import logging
import math
import time

from app.core.config import settings
from app.services import nasa_power_service

logger = logging.getLogger(__name__)


def _fetch_mock(lat: float, lon: float) -> float:
    """
    Generate deterministic but time-varying simulated soil moisture.

    This is intended for local development, demonstrations, testing,
    or explicitly enabled mock fallback operation.
    """

    seed = int((lat * 1000 + lon * 1000)) % 89

    t = time.time() / 3600

    base = 30 + seed % 35

    wave = 25 * max(
        0,
        math.sin(t / 8 + seed * 0.7),
    )

    return round(
        min(
            100.0,
            max(
                5.0,
                base + wave,
            ),
        ),
        1,
    )


def get_latest_soil_moisture(
    lat: float,
    lon: float,
) -> float:
    """
    Return the latest soil-moisture percentage for a location.

    Behavior:

        USE_MOCK_IMD=true
            -> explicit mock mode

        USE_MOCK_IMD=false
            -> NASA POWER real environmental data

        NASA POWER fails and ALLOW_MOCK_FALLBACK=true
            -> use simulated soil moisture

        NASA POWER fails and ALLOW_MOCK_FALLBACK=false
            -> raise RuntimeError

    Production should keep mock fallback disabled so simulated soil
    moisture cannot be mistaken for real environmental observations.
    """

    # ---------------------------------------------------------
    # Explicit mock mode
    # ---------------------------------------------------------
    if settings.USE_MOCK_IMD:
        logger.info(
            "Using explicitly enabled mock soil-moisture data "
            "for (%s, %s).",
            lat,
            lon,
        )

        return _fetch_mock(lat, lon)

    # ---------------------------------------------------------
    # Real provider: NASA POWER
    # ---------------------------------------------------------
    try:
        environmental_data = nasa_power_service.fetch(
            lat,
            lon,
        )

        logger.info(
            "Soil moisture obtained from NASA POWER for (%s, %s).",
            lat,
            lon,
        )

        return environmental_data.soil_moisture_pct

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "NASA POWER soil-moisture fetch failed for (%s, %s): %s",
            lat,
            lon,
            exc,
        )

        # -----------------------------------------------------
        # Optional mock fallback
        # -----------------------------------------------------
        if settings.ALLOW_MOCK_FALLBACK:
            logger.warning(
                "ALLOW_MOCK_FALLBACK=true, so simulated soil moisture "
                "will be used for (%s, %s).",
                lat,
                lon,
            )

            return _fetch_mock(lat, lon)

        # -----------------------------------------------------
        # Production-safe failure
        # -----------------------------------------------------
        logger.error(
            "NASA POWER soil-moisture provider failed for (%s, %s), "
            "and mock fallback is disabled.",
            lat,
            lon,
        )

        raise RuntimeError(
            f"No real soil-moisture data available for "
            f"({lat}, {lon}). Mock fallback is disabled. "
            f"Provider error: {exc}"
        ) from exc
