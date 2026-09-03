import json
from pathlib import Path

from app.ml.predictor import RiskFeatures, predict

SAMPLE_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "sample" / "sample_readings.json"


def _load_sample_readings() -> list[dict]:
    if not SAMPLE_DATA_PATH.exists():
        return []
    with open(SAMPLE_DATA_PATH, "r") as f:
        return json.load(f)


def get_dashboard_readings() -> list[dict]:
    """Return every sample location with a freshly computed risk assessment."""
    readings = _load_sample_readings()
    results = []
    for r in readings:
        features = RiskFeatures(
            rainfall_mm_24h=r["rainfall_mm_24h"],
            soil_moisture_pct=r["soil_moisture_pct"],
            slope_deg=r["slope_deg"],
            temperature_c=r.get("temperature_c"),
        )
        risk = predict(features)
        results.append(
            {
                **r,
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
                "contributing_factors": risk.contributing_factors,
                "recommendation": risk.recommendation,
            }
        )
    return results


def assess_custom_reading(payload: dict) -> dict:
    """Run the predictor against a caller-supplied reading (manual entry / IoT payload)."""
    features = RiskFeatures(
        rainfall_mm_24h=payload["rainfall_mm_24h"],
        soil_moisture_pct=payload["soil_moisture_pct"],
        slope_deg=payload["slope_deg"],
        temperature_c=payload.get("temperature_c"),
    )
    risk = predict(features)
    return {
        "risk_score": risk.risk_score,
        "risk_level": risk.risk_level,
        "contributing_factors": risk.contributing_factors,
        "recommendation": risk.recommendation,
    }
