"""Central configuration for the SANRAKSHA backend.

All deployment-specific values are read from environment variables.
Satellite credentials are backend-only and must never be exposed to the
frontend bundle.
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings:
    _raw_database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BACKEND_DIR / 'data' / 'sanraksha.db'}",
    )

    DATABASE_URL: str = (
        _raw_database_url.replace("postgres://", "postgresql://", 1)
        if _raw_database_url.startswith("postgres://")
        else _raw_database_url
    )

    # --- Environmental data ---
    USE_MOCK_IMD: bool = os.getenv("USE_MOCK_IMD", "true").lower() == "true"
    IMD_API_BASE_URL: str = os.getenv(
        "IMD_API_BASE_URL",
        "https://mausam.imd.gov.in/api",
    )
    IMD_API_KEY: str = os.getenv("IMD_API_KEY", "")

    # NASA POWER provides environmental/reanalysis data, not raw/live
    # satellite imagery.
    NASA_POWER_BASE_URL: str = os.getenv(
        "NASA_POWER_BASE_URL",
        "https://power.larc.nasa.gov/api",
    )

    ALLOW_MOCK_FALLBACK: bool = (
        os.getenv("ALLOW_MOCK_FALLBACK", "false").lower() == "true"
    )

    # --- Copernicus Data Space / Sentinel Hub ---
    # Keep these values server-side. Never expose them through VITE_* vars.
    SENTINEL_HUB_BASE_URL: str = os.getenv(
        "SENTINEL_HUB_BASE_URL",
        "https://sh.dataspace.copernicus.eu",
    )
    SENTINEL_HUB_TOKEN_URL: str = os.getenv(
        "SENTINEL_HUB_TOKEN_URL",
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
    )
    COPERNICUS_CLIENT_ID: str = os.getenv("COPERNICUS_CLIENT_ID", "")
    COPERNICUS_CLIENT_SECRET: str = os.getenv("COPERNICUS_CLIENT_SECRET", "")

    # Latest-available observation search/rendering controls.
    SATELLITE_LOOKBACK_DAYS: int = int(
        os.getenv("SATELLITE_LOOKBACK_DAYS", "30")
    )
    SATELLITE_MAX_CLOUD_COVER_PCT: float = float(
        os.getenv("SATELLITE_MAX_CLOUD_COVER_PCT", "80")
    )
    SATELLITE_AOI_RADIUS_DEG: float = float(
        os.getenv("SATELLITE_AOI_RADIUS_DEG", "0.04")
    )
    SATELLITE_IMAGE_WIDTH: int = int(
        os.getenv("SATELLITE_IMAGE_WIDTH", "768")
    )
    SATELLITE_IMAGE_HEIGHT: int = int(
        os.getenv("SATELLITE_IMAGE_HEIGHT", "512")
    )
    SATELLITE_CACHE_SECONDS: int = int(
        os.getenv("SATELLITE_CACHE_SECONDS", "600")
    )

    # --- ML model ---
    TRAINED_MODEL_PATH: str = os.getenv(
        "TRAINED_MODEL_PATH",
        str(
            BACKEND_DIR.parent
            / "ml"
            / "models"
            / "landslide_model.pkl"
        ),
    )

    # --- Background sync ---
    SYNC_INTERVAL_MINUTES: int = int(
        os.getenv("SYNC_INTERVAL_MINUTES", "30")
    )
    # Worker threads are used only for outbound environmental-data requests.
    # SQLAlchemy database writes remain on the sync thread.
    SYNC_FETCH_WORKERS: int = max(
        1, int(os.getenv("SYNC_FETCH_WORKERS", "5"))
    )
    ENABLE_SCHEDULER: bool = (
        os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
    )

    # --- MQTT ---
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_TOPIC_PREFIX: str = os.getenv(
        "MQTT_TOPIC_PREFIX",
        "sanraksha/sensors",
    )

    # --- Ingest authentication ---
    INGEST_TOKEN: str = os.getenv("INGEST_TOKEN", "dev-ingest-token")

    # --- CORS ---
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "*")

    # --- Admin authentication ---
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")


settings = Settings()
