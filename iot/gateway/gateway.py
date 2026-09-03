"""
IoT gateway.

Runs on-site (a Raspberry Pi, typically) alongside the LoRa/MQTT
infrastructure. It subscribes to every sensor node's MQTT topic and
forwards each reading to the backend's /api/ingest endpoint over HTTP,
so the sensor nodes themselves never need to know the backend's address
or handle HTTP/auth — they just publish to the local broker.

Run:
    python iot/gateway/gateway.py
"""

import logging
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from communication.mqtt_client import MqttClient  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("gateway")

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "sanraksha/sensors")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
INGEST_TOKEN = os.getenv("INGEST_TOKEN", "dev-ingest-token")


def forward_to_backend(topic: str, payload: dict):
    location_id = topic.split("/")[-1]
    body = {
        "location_id": location_id,
        "rainfall_mm_24h": payload.get("rainfall_mm_24h"),
        "soil_moisture_pct": payload.get("soil_moisture_pct"),
        "temperature_c": payload.get("temperature_c"),
        "token": INGEST_TOKEN,
    }
    try:
        resp = requests.post(f"{BACKEND_URL}/api/ingest", json=body, timeout=5)
        resp.raise_for_status()
        logger.info("Ingested %s -> %s", location_id, resp.json())
    except requests.RequestException as exc:
        logger.error("Failed to forward reading for %s: %s", location_id, exc)


def main():
    client = MqttClient(MQTT_HOST, MQTT_PORT, client_id="sanraksha-gateway")
    logger.info("Gateway starting, broker=%s:%s, backend=%s", MQTT_HOST, MQTT_PORT, BACKEND_URL)
    client.subscribe(f"{TOPIC_PREFIX}/#", forward_to_backend)
    client.loop_forever()


if __name__ == "__main__":
    main()
