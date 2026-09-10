"""
Central configuration for the SANRAKSHA backend.

Everything here is read from environment variables with sensible local-dev
defaults.

Local development:
    USE_MOCK_IMD=true
    ALLOW_MOCK_FALLBACK=true

Production:
    USE_MOCK_IMD=false
    ALLOW_MOCK_FALLBACK=false

In production, real provider failures must be visible instead of silently
being replaced with simulated environmental data.
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings:
    # --- Database ---
    # SQLAlchemy 2.x requires the "postgresql://" scheme. Render and some
    # providers may return the older "postgres://" scheme.
    _raw_database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BACKEND_DIR / 'data' / 'sanraksha.db'}",
    )

    DATABASE_URL: str = (
        _raw_database_url.replace("postgres://", "postgresql://", 1)
        if _raw_database_url.startswith("postgres://")
        else _raw_database_url
    )

    # --- Environmental data source ---
    #
    # true:
    #     Use simulated rainfall/environmental data.
    #
    # false:
    #     Use real environmental data providers.
    USE_MOCK_IMD: bool = (
        os.getenv("USE_MOCK_IMD", "true").lower() == "true"
    )

    IMD_API_BASE_URL: str = os.getenv(
        "IMD_API_BASE_URL",
        "https://mausam.imd.gov.in/api",
    )

    IMD_API_KEY: str = os.getenv("IMD_API_KEY", "")

    # NASA POWER is the primary public, keyless environmental-data provider
    # when USE_MOCK_IMD=false.
    #
    # NASA POWER provides MERRA-2/reanalysis-derived environmental data.
    # It should not be described as raw/live satellite imagery.
    NASA_POWER_BASE_URL: str = os.getenv(
        "NASA_POWER_BASE_URL",
        "https://power.larc.nasa.gov/api",
    )

    # --- Mock fallback control ---
    #
    # IMPORTANT:
    # Production should keep this false.
    #
    # If false, failure of a real provider raises an error instead of silently
    # returning simulated data.
    #
    # If true, mock data may be used after a real-provider failure. This is
    # useful for local demonstrations and development.
    ALLOW_MOCK_FALLBACK: bool = (
        os.getenv("ALLOW_MOCK_FALLBACK", "false").lower() == "true"
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

    ENABLE_SCHEDULER: bool = (
        os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
    )

    # --- MQTT (IoT gateway) ---
    MQTT_BROKER_HOST: str = os.getenv(
        "MQTT_BROKER_HOST",
        "localhost",
    )

    MQTT_BROKER_PORT: int = int(
        os.getenv("MQTT_BROKER_PORT", "1883")
    )

    MQTT_TOPIC_PREFIX: str = os.getenv(
        "MQTT_TOPIC_PREFIX",
        "sanraksha/sensors",
    )

    # --- Ingest authentication ---
    #
    # Shared secret used by the IoT gateway for protected ingestion.
    INGEST_TOKEN: str = os.getenv(
        "INGEST_TOKEN",
        "dev-ingest-token",
    )

    # --- CORS ---
    #
    # Comma-separated list of allowed origins, for example:
    #
    # https://sanraksha-frontend.onrender.com,http://localhost:5173
    #
    # "*" is convenient for local development.
    CORS_ALLOWED_ORIGINS: str = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "*",
    )

    # --- Admin authentication ---
    #
    # Empty string disables admin-key protection.
    # Production deployments should set ADMIN_API_KEY.
    ADMIN_API_KEY: str = os.getenv(
        "ADMIN_API_KEY",
        "",
    )


settings = Settings()
