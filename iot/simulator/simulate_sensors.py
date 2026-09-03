"""
Simulates real sensor nodes (see ../sensor_node/*.ino for the actual
firmware these stand in for) by publishing plausible, slowly-drifting
rainfall/soil-moisture/temperature readings to MQTT every few seconds —
including an optional simulated storm event so you can watch risk levels
climb in the dashboard in real time.

Run:
    python iot/simulator/simulate_sensors.py
    python iot/simulator/simulate_sensors.py --storm munnar-01   # spike one location
"""

import argparse
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from communication.mqtt_client import MqttClient  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("simulator")

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "sanraksha/sensors")

# Must match the location_ids seeded in backend/data/sample/sample_readings.json
LOCATIONS = ["munnar-01", "wayanad-02", "nilgiris-03", "darjeeling-04", "shimla-05"]


class SensorState:
    """Tracks each location's last reading so values drift gradually
    instead of jumping randomly between publishes."""

    def __init__(self):
        self.rainfall = {loc: random.uniform(10, 60) for loc in LOCATIONS}
        self.soil_moisture = {loc: random.uniform(30, 60) for loc in LOCATIONS}
        self.temperature = {loc: random.uniform(16, 24) for loc in LOCATIONS}

    def step(self, loc: str, storm: bool = False):
        drift = random.uniform(-5, 5)
        if storm:
            drift = random.uniform(20, 40)  # simulated cloudburst

        self.rainfall[loc] = max(0, min(300, self.rainfall[loc] + drift))
        self.soil_moisture[loc] = max(5, min(100, self.soil_moisture[loc] + drift * 0.3))
        self.temperature[loc] = max(5, min(35, self.temperature[loc] + random.uniform(-0.5, 0.5)))

        return {
            "rainfall_mm_24h": round(self.rainfall[loc], 1),
            "soil_moisture_pct": round(self.soil_moisture[loc], 1),
            "temperature_c": round(self.temperature[loc], 1),
            "ts": datetime.now(timezone.utc).isoformat(),
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--storm", help="location_id to simulate a storm/spike at", default=None)
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between publishes")
    parser.add_argument("--rounds", type=int, default=6, help="number of publish rounds")
    args = parser.parse_args()

    client = MqttClient(MQTT_HOST, MQTT_PORT, client_id="sanraksha-simulator").connect()
    state = SensorState()

    logger.info("Simulating %d sensor nodes, broker=%s:%s", len(LOCATIONS), MQTT_HOST, MQTT_PORT)
    for round_num in range(args.rounds):
        for loc in LOCATIONS:
            storm = args.storm == loc
            reading = state.step(loc, storm=storm)
            client.publish(f"{TOPIC_PREFIX}/{loc}", reading)
        time.sleep(args.interval)

    client.disconnect()
    logger.info("Simulation finished (%d rounds)", args.rounds)


if __name__ == "__main__":
    main()
