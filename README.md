# Sanraksha — Landslide Early Warning System

**Phase 1: basic working prototype.**

Rainfall / soil-moisture / slope readings → FastAPI backend → rule-based
risk model → risk level → React dashboard.

```
Rainfall = 182 mm
Soil Moisture = 84%
Slope = 39°
        ↓
  risk model (backend/app/ml/predictor.py)
        ↓
  CRITICAL — risk score 98
        ↓
  React dashboard (color-coded card + map marker + recommendation)
```

This repo currently contains the Phase 1 slice only:

```
SANRAKSHA/
├── backend/
│   ├── app/
│   │   ├── main.py                     FastAPI app + CORS
│   │   ├── schemas.py                  Pydantic request/response models
│   │   ├── api/routes/prediction.py    GET /api/dashboard, POST /api/predict
│   │   ├── ml/predictor.py             Rule-based risk scoring model
│   │   └── services/prediction_service.py
│   ├── data/sample/sample_readings.json
│   ├── requirements.txt
│   └── README.md
│
├── frontend/web-dashboard/
│   ├── src/
│   │   ├── App.jsx, main.jsx
│   │   ├── pages/Dashboard.jsx
│   │   ├── components/RiskCard.jsx, RiskMap.jsx
│   │   ├── services/api.js
│   │   └── styles/global.css
│   ├── package.json, vite.config.js, index.html
│   └── README.md
│
└── README.md                            (this file)
```

Later phases (real IMD/satellite data ingestion, a trained ML model, a
database, IoT sensor nodes, mobile app, alerting) are described in the
original architecture doc but not built yet — see "Roadmap" below.

## Quickstart

Two terminals:

```bash
# Terminal 1 — backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend/web-dashboard
npm install
npm run dev
```

Open `http://localhost:5173`. You should see five sample hill-region
locations with live-computed risk levels, an SVG map, and a form to test
your own rainfall/soil-moisture/slope reading against the model.

## How the risk model works

`backend/app/ml/predictor.py` is a rule-based scorer (0–100), not yet a
trained ML model:

- Rainfall (last 24h) contributes up to 40 points, ramping up sharply past 100mm
- Soil moisture contributes up to 30 points, ramping up sharply past 70%
- Slope angle contributes up to 30 points, ramping up sharply past 30°
- An extra penalty applies when rainfall and soil moisture are **both**
  high at once — the classic landslide trigger

Score bands: `LOW` (0–24), `MODERATE` (25–49), `HIGH` (50–74), `CRITICAL`
(75–100).

This keeps the system fully functional and explainable today, while
matching the interface (`RiskFeatures` in → `RiskResult` out) that a
trained model will use in a later phase — see `backend/README.md`.

## Roadmap (not built yet)

- **Phase 2 — real data:** ingest live IMD rainfall data, persist readings
  in a database (Postgres/PostGIS), replace the rule-based scorer with a
  trained model (`ml/training/`, scikit-learn or similar).
- **Phase 3 — IoT:** soil-moisture and rain sensor nodes (ESP32/Arduino)
  publishing over MQTT/LoRa to a gateway that feeds the backend directly.
- **Later:** satellite imagery ingestion, GIS slope/elevation analysis, SMS
  and siren alerting, the Flutter mobile app, authentication, and the
  reports module — as laid out in the original full architecture.

## License

Not yet specified — add a LICENSE file before making this repository public
if you intend others to reuse the code.
