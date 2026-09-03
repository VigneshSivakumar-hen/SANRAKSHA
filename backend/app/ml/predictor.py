"""
Phase 1 landslide risk predictor.

This is a transparent, rule-based scoring model that stands in for the
trained ML model referenced in the full architecture
(ml/models/landslide_prediction_model.pkl). It takes the same feature
shape the real model will eventually take, so swapping in a trained
model later only means changing `predict()` internals, not the API.

Scoring logic (0-100 risk score):
  - Rainfall (24h)   -> up to 40 points, rises sharply above 100mm
  - Soil moisture     -> up to 30 points, rises sharply above 70%
  - Slope angle       -> up to 30 points, rises sharply above 30 degrees
  - Small extra weight if rainfall AND soil moisture are BOTH high,
    since saturated soil + heavy rain is the classic landslide trigger.
"""

from dataclasses import dataclass


@dataclass
class RiskFeatures:
    rainfall_mm_24h: float
    soil_moisture_pct: float
    slope_deg: float
    temperature_c: float | None = None


@dataclass
class RiskResult:
    risk_score: float
    risk_level: str
    contributing_factors: list[str]
    recommendation: str


def _rainfall_score(mm: float) -> float:
    if mm <= 0:
        return 0.0
    # Piecewise ramp: gentle up to 50mm, steep from 50-150mm, capped at 40
    if mm < 50:
        return round((mm / 50) * 15, 1)
    if mm < 150:
        return round(15 + ((mm - 50) / 100) * 20, 1)
    return 40.0


def _soil_moisture_score(pct: float) -> float:
    pct = max(0.0, min(pct, 100.0))
    if pct < 40:
        return round((pct / 40) * 8, 1)
    if pct < 75:
        return round(8 + ((pct - 40) / 35) * 15, 1)
    return round(23 + min((pct - 75) / 25, 1) * 7, 1)


def _slope_score(deg: float) -> float:
    deg = max(0.0, min(deg, 90.0))
    if deg < 15:
        return round((deg / 15) * 5, 1)
    if deg < 35:
        return round(5 + ((deg - 15) / 20) * 18, 1)
    return round(23 + min((deg - 35) / 20, 1) * 7, 1)


def _risk_level(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MODERATE"
    return "LOW"


def _recommendation(level: str) -> str:
    return {
        "CRITICAL": "Evacuate the area immediately and alert local disaster management authorities.",
        "HIGH": "Restrict access to the slope, notify residents, and monitor conditions continuously.",
        "MODERATE": "Increase monitoring frequency and prepare contingency/evacuation plans.",
        "LOW": "Continue routine monitoring. No immediate action required.",
    }[level]


def predict(features: RiskFeatures) -> RiskResult:
    rainfall_pts = _rainfall_score(features.rainfall_mm_24h)
    soil_pts = _soil_moisture_score(features.soil_moisture_pct)
    slope_pts = _slope_score(features.slope_deg)

    score = rainfall_pts + soil_pts + slope_pts

    factors = []
    if rainfall_pts >= 25:
        factors.append("Heavy rainfall in the last 24 hours")
    elif rainfall_pts >= 12:
        factors.append("Moderate rainfall accumulation")

    if soil_pts >= 20:
        factors.append("Soil is near saturation")
    elif soil_pts >= 10:
        factors.append("Elevated soil moisture")

    if slope_pts >= 20:
        factors.append("Steep slope angle")
    elif slope_pts >= 10:
        factors.append("Moderately steep terrain")

    # Compound trigger: saturated soil + heavy rain together, capped at 100
    if features.rainfall_mm_24h > 100 and features.soil_moisture_pct > 70:
        score = min(score + 8, 100)
        factors.append("Compound trigger: saturated soil during heavy rainfall")

    score = round(min(score, 100.0), 1)
    level = _risk_level(score)

    if not factors:
        factors.append("All monitored conditions within normal range")

    return RiskResult(
        risk_score=score,
        risk_level=level,
        contributing_factors=factors,
        recommendation=_recommendation(level),
    )
