# Sanraksha — Landslide Early Warning System

**Phases 1–3 built and tested: prototype, real-data pipeline + trained ML
model, and an IoT sensor-to-dashboard flow.**

```
IoT sensor node (real ESP32, or the simulator)
        │  MQTT
        ▼
   Gateway  ──────────┐
                       │
IMD rainfall (mock)    │  HTTP
Satellite soil (mock)  │
        │  scheduled/manual sync
        ▼              ▼
              Backend (FastAPI)
              stores Reading → SQLite
              runs trained RandomForest (fallback: rule-based scorer)
              stores Prediction
                       │
                       ▼
              React dashboard — map, risk cards, history, manual test form
```

## What's built

```
SANRAKSHA/
├── backend/                          FastAPI app
│   ├── app/
│   │   ├── main.py                   App startup: creates tables, seeds locations, optional scheduler
│   │   ├── core/
│   │   │   ├── config.py             All settings, env-var driven
│   │   │   ├── database.py           SQLAlchemy engine/session (SQLite by default)
│   │   │   └── scheduler.py          Optional periodic IMD/satellite sync (APScheduler)
│   │   ├── models/__init__.py        ORM: Location, Reading, Prediction
│   │   ├── schemas.py                Pydantic request/response models
│   │   ├── api/routes/prediction.py  /api/dashboard, /api/predict, /api/sync/run, /api/ingest, /api/locations/{id}/history
│   │   ├── ml/predictor.py           Trained-model inference, with rule-based fallback
│   │   └── services/
│   │       ├── imd_service.py        Rainfall adapter (mock by default; real IMD client shape included)
│   │       ├── satellite_service.py  Soil-moisture adapter (mock by default)
│   │       └── prediction_service.py Orchestrates DB + predictor
│   ├── data/sample/sample_readings.json   Seed data for first run
│   └── requirements.txt
│
├── ml/                                Training pipeline (separate from runtime inference)
│   ├── training/generate_dataset.py   Synthetic-but-physically-plausible landslide dataset
│   ├── training/train.py              Trains + saves the RandomForest model
│   ├── datasets/landslide_training_data.csv
│   └── models/landslide_model.pkl, metrics.json
│
├── iot/                                Phase 3: sensors → MQTT → gateway → backend
│   ├── sensor_node/                    ESP32 firmware (soil moisture, rain, temperature)
│   ├── simulator/simulate_sensors.py   Simulated sensors for testing without hardware
│   ├── gateway/gateway.py              Subscribes to MQTT, forwards to /api/ingest
│   └── communication/                  mqtt_client.py (used, tested) + lora_handler.py (interface only)
│
├── frontend/web-dashboard/             React + Vite dashboard
│
└── README.md                           (this file)
```

## Quickstart — full stack

```bash
# 1. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
# 2. Frontend (separate terminal)
cd frontend/web-dashboard
npm install
npm run dev
```

Open `http://localhost:5173`. On first run the backend seeds 5 sample
hill-region locations (Kerala, Tamil Nadu, West Bengal, Himachal Pradesh)
with an initial reading each.

Pull fresh (mock) IMD + satellite data for every location:

```bash
curl -X POST http://localhost:8000/api/sync/run
```

See `iot/README.md` to run the simulated sensor → MQTT → gateway → backend
pipeline (tested end-to-end with a local mosquitto broker), and
`ml/README.md` to retrain the model.

## The risk model

`backend/app/ml/predictor.py` tries a trained RandomForest classifier first
(`ml/models/landslide_model.pkl`, ROC-AUC ~0.82 — see `ml/README.md` for
what it was trained on and why). If that model file is missing or fails to
load, it falls back automatically to a transparent rule-based scorer, and
every API response says which one produced the result via `model_used`
(`"trained"` or `"rule_based"`) — the system degrades gracefully rather
than breaking if a model artifact isn't present.

Score bands: `LOW` (0–24), `MODERATE` (25–49), `HIGH` (50–74), `CRITICAL`
(75–100).

## API reference

| Method | Path                              | Description                                              |
|--------|------------------------------------|------------------------------------------------------------|
| GET    | `/api/dashboard`                  | Latest reading + risk for every location                  |
| GET    | `/api/locations/{id}/history`     | Recent readings + predictions for one location             |
| POST   | `/api/predict`                    | Score a manually-entered reading (not persisted)           |
| POST   | `/api/sync/run`                   | Manually trigger an IMD + satellite pull for all locations |
| POST   | `/api/ingest`                     | Sensor reading ingest, used by the IoT gateway              |

## What's genuinely tested vs. reference-only

**Tested end-to-end in this environment:**
- Backend startup, DB seeding, dashboard, manual predict, sync, history
- Trained model loading and inference, with fallback verified by design
- Full IoT chain: sensor simulator → real local MQTT broker (mosquitto) →
  gateway → `/api/ingest` → database → updated risk level, including a
  simulated storm escalating one location from MODERATE to CRITICAL

**Reference code, not executable here (needs real infrastructure/hardware):**
- `imd_service.py` / `satellite_service.py`'s real API branches — this
  sandbox can't reach live government weather APIs; mock providers are
  used by default and are what's actually exercised
- `iot/sensor_node/*.ino` — ESP32 firmware; needs real hardware to flash
  and calibrate, see `iot/README.md`
- `iot/communication/lora_handler.py` — documents the intended interface
  for a LoRa-to-gateway bridge; not implemented against real LoRa radios

## Roadmap (not built yet)

- GIS slope/elevation analysis from real elevation data (currently slope
  is a static per-location value)
- SMS/siren alerting, the Flutter mobile app, authentication, the reports
  module — as laid out in the original full architecture
- Postgres/PostGIS instead of SQLite for a real multi-node deployment

## License

Not yet specified — add a LICENSE file before making this repository public
if you intend others to reuse the code.
