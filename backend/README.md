# Sanraksha backend (Phase 1)

FastAPI service exposing a landslide risk assessment API.

## Run locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

## Endpoints

| Method | Path             | Description                                                    |
|--------|------------------|------------------------------------------------------------------|
| GET    | `/health`        | Liveness check                                                  |
| GET    | `/api/dashboard` | All sample monitoring locations with a live risk assessment     |
| POST   | `/api/predict`   | Run the risk model against a single reading you supply          |

Example:

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"rainfall_mm_24h": 180, "soil_moisture_pct": 82, "slope_deg": 38}'
```

## About the prediction model

`app/ml/predictor.py` is a transparent, rule-based scoring model — it weighs
rainfall, soil moisture, and slope angle into a 0–100 risk score with an
extra penalty when rainfall and soil moisture are both high at once (the
classic landslide trigger combination). It's a deliberate stand-in for the
trained ML model referenced in the full architecture
(`ml/models/landslide_prediction_model.pkl`).

To swap in a real trained model later: keep `RiskFeatures` and `RiskResult`
as the interface, and replace the body of `predict()` with a call to your
loaded model. Nothing in the API layer needs to change.

## Sample data

`data/sample/sample_readings.json` holds five hill-region locations across
Kerala, Tamil Nadu, West Bengal, and Himachal Pradesh, used to seed
`/api/dashboard`.
