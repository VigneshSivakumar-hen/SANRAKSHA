"""
Central configuration for the Sanraksha backend.

Everything here is read from environment variables with sane local-dev
defaults, so the app runs out of the box with `USE_MOCK_IMD=true` and a
local SQLite file, and can be pointed at real infrastructure later just by
setting env vars (see .env.example).
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings:
    # --- Database ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'data' / 'sanraksha.db'}"
    )

    # --- IMD (India Meteorological Department) data source ---
    # When USE_MOCK_IMD is true, imd_service returns realistic simulated
    # rainfall instead of calling the real IMD API. Flip this once you have
    # real IMD/data.gov.in API credentials.
    USE_MOCK_IMD: bool = os.getenv("USE_MOCK_IMD", "true").lower() == "true"
    IMD_API_BASE_URL: str = os.getenv("IMD_API_BASE_URL", "https://mausam.imd.gov.in/api")
    IMD_API_KEY: str = os.getenv("IMD_API_KEY", "")

    # --- ML model ---
    TRAINED_MODEL_PATH: str = os.getenv(
        "TRAINED_MODEL_PATH", str(BACKEND_DIR.parent / "ml" / "models" / "landslide_model.pkl")
    )

    # --- Background sync ---
    SYNC_INTERVAL_MINUTES: int = int(os.getenv("SYNC_INTERVAL_MINUTES", "30"))
    ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"

    # --- MQTT (IoT gateway) ---
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_TOPIC_PREFIX: str = os.getenv("MQTT_TOPIC_PREFIX", "sanraksha/sensors")

    # --- Ingest auth (shared secret the gateway sends, cheap protection for Phase 3) ---
    INGEST_TOKEN: str = os.getenv("INGEST_TOKEN", "dev-ingest-token")


settings = Settings()
