# Sanraksha IoT layer (Phase 3)

Sensor nodes → MQTT → gateway → backend `/api/ingest`.

```
ESP32 node (real, or simulator/simulate_sensors.py)
        │  publishes JSON to  sanraksha/sensors/<location_id>
        ▼
   MQTT broker (mosquitto)
        │  gateway subscribes to sanraksha/sensors/#
        ▼
 gateway/gateway.py
        │  POSTs to backend /api/ingest
        ▼
   Backend (stores Reading + runs prediction)
```

## Run the simulated pipeline (no hardware needed)

```bash
# 1. MQTT broker
sudo apt-get install -y mosquitto mosquitto-clients
mosquitto -p 1883 &

# 2. Backend (from repo root, separate terminal)
cd backend && uvicorn app.main:app --reload --port 8000 &

# 3. Gateway
pip install -r iot/requirements.txt
python iot/gateway/gateway.py &

# 4. Simulate sensor nodes, with an optional storm at one location
python iot/simulator/simulate_sensors.py --storm munnar-01 --interval 5 --rounds 12
```

Watch the gateway's terminal log each ingested reading and risk level, or
poll `GET /api/locations/munnar-01/history` to see the timeline.

## Real hardware (Phase 3, firmware not yet flashed/tested)

`sensor_node/` contains ESP32 firmware for a combined soil-moisture +
rain + temperature node:

- `sensor_config.h` — WiFi, MQTT broker address, pin assignments, and
  ADC calibration constants. **Edit this before flashing** — the ADC
  wet/dry calibration values in particular vary per sensor unit.
- `soil_moisture.ino` — main sketch: connects to WiFi/MQTT, reads soil
  moisture + temperature, publishes a combined reading every
  `PUBLISH_INTERVAL_MS`.
- `rain_sensor.ino` — rain reading logic, same sketch (Arduino IDE
  combines every `.ino` file in a folder into one sketch).

Required Arduino libraries: PubSubClient, DHT sensor library (Adafruit),
ArduinoJson.

The rain sensor code notes an important caveat: cheap analog "raindrop"
boards measure instantaneous wetness, not real cumulative mm — swap in a
tipping-bucket gauge for accurate 24h rainfall totals in a real
deployment.

For sites without WiFi reach, `communication/lora_handler.py` documents
(but does not implement — no LoRa hardware available here to test
against) the intended shape of a LoRa-to-MQTT bridge that would feed the
same gateway.

## Ingest auth

The gateway sends a shared token (`INGEST_TOKEN`, default
`dev-ingest-token`) with every `/api/ingest` call — change it in both the
backend's environment and the gateway's before exposing this beyond your
local machine.
