"""Central configuration for the SANRAKSHA backend."""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings:
    # --- Database ---
    _raw_database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'data' / 'sanraksha.db'}"
    )
    DATABASE_URL: str = (
        _raw_database_url.replace("postgres://", "postgresql://", 1)
        if _raw_database_url.startswith("postgres://")
        else _raw_database_url
    )

    # --- Environmental data sources ---
    # Mock values are for local demos only. Production must leave both false
    # so unavailable providers remain visible rather than becoming fake data.
    USE_MOCK_IMD: bool = os.getenv("USE_MOCK_IMD", "true").lower() == "true"
    USE_MOCK_SATELLITE: bool = os.getenv("USE_MOCK_SATELLITE", "true").lower() == "true"
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

    # --- Ingest auth ---
    INGEST_TOKEN: str = os.getenv("INGEST_TOKEN", "dev-ingest-token")

    # --- Admin auth ---
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")


settings = Settings()
