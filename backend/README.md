# Sanraksha backend

FastAPI service: persists readings, runs the risk model, and exposes the
dashboard/sync/ingest API.

## Run locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

`http://localhost:8000/docs` has interactive API docs. On first run the app
creates `data/sanraksha.db` (SQLite) and seeds 5 sample locations.

Copy `../.env.example` to `.env` (or export the same vars) to override any
default — database URL, mock vs. real IMD, scheduler, MQTT/ingest settings.

## Endpoints

| Method | Path                          | Description                                                  |
|--------|-------------------------------|----------------------------------------------------------------|
| GET    | `/health`                     | Liveness check                                                 |
| GET    | `/api/dashboard`               | Latest reading + risk assessment for every location            |
| GET    | `/api/locations/{id}/history`  | Recent readings + predictions for one location, newest first   |
| POST   | `/api/predict`                 | Score a manually-supplied reading (not persisted)               |
| POST   | `/api/sync/run`                | Pull fresh IMD + satellite data for every location, store it    |
| POST   | `/api/ingest`                  | Store + score a sensor reading (used by `iot/gateway/gateway.py`) |

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"rainfall_mm_24h": 180, "soil_moisture_pct": 82, "slope_deg": 38}'
```

## Data flow

Three sources write `Reading` rows, all scored the same way:

- **`seed`** — bootstrap data from `data/sample/sample_readings.json`, once, on first run
- **`sync`** — `app/services/imd_service.py` + `satellite_service.py`, triggered by
  `POST /api/sync/run` or the background scheduler (`ENABLE_SCHEDULER=true`)
- **`iot`** — the gateway posting to `/api/ingest`, see `../iot/README.md`

Every `Reading` gets a `Prediction` (score, level, contributing factors,
recommendation) computed immediately and stored alongside it.

## The prediction model

`app/ml/predictor.py` loads the trained model from `../ml/models/landslide_model.pkl`
(see `../ml/README.md`) at first use. If that file is missing or fails to
load, it transparently falls back to a rule-based scorer — both paths
share the same `RiskFeatures` in / `RiskResult` out interface, and the
response always reports which one ran via `model_used`.

## IMD / satellite adapters

`app/services/imd_service.py` and `satellite_service.py` default to
realistic mock data (`USE_MOCK_IMD=true`). Each has a `_fetch_real()`
function with the intended real-API call shape — point it at actual IMD /
data.gov.in / satellite endpoints and flip `USE_MOCK_IMD=false` when you
have credentials; nothing else in the app needs to change.
