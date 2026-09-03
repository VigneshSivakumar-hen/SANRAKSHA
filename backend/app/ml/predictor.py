"""
Landslide risk predictor.

Phase 2 adds a trained RandomForest classifier (ml/models/landslide_model.pkl,
produced by ml/training/train.py on a synthetic-but-physically-plausible
dataset — see ml/training/generate_dataset.py for the assumptions it
encodes). The rule-based scorer from Phase 1 is kept as an automatic
fallback: if the trained model file is missing or fails to load, predict()
transparently falls back to it and says so in RiskResult.model_used, so the
API never breaks because a model artifact wasn't shipped.
"""

import logging
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)

_trained_model = None
_trained_features = None
_load_attempted = False


def _load_trained_model():
    """Lazily load the trained model once per process. Returns None (and
    logs a warning) if it isn't available, so callers always fall back
    cleanly to the rule-based scorer."""
    global _trained_model, _trained_features, _load_attempted
    if _load_attempted:
        return _trained_model
    _load_attempted = True
    try:
        import joblib

        bundle = joblib.load(settings.TRAINED_MODEL_PATH)
        _trained_model = bundle["model"]
        _trained_features = bundle["features"]
        logger.info("Loaded trained landslide model from %s", settings.TRAINED_MODEL_PATH)
    except Exception as exc:  # noqa: BLE001 - any load failure should just fall back
        logger.warning("Trained model unavailable (%s); using rule-based fallback.", exc)
        _trained_model = None
    return _trained_model


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
    model_used: str = "rule_based"  # "trained" | "rule_based"


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


def _contributing_factors(features: RiskFeatures) -> list[str]:
    """Human-readable factors, derived from the same thresholds the
    rule-based scorer uses, regardless of which model produced the score.
    Keeps explanations consistent whichever model answered."""
    factors = []
    rainfall_pts = _rainfall_score(features.rainfall_mm_24h)
    soil_pts = _soil_moisture_score(features.soil_moisture_pct)
    slope_pts = _slope_score(features.slope_deg)

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

    if features.rainfall_mm_24h > 100 and features.soil_moisture_pct > 70:
        factors.append("Compound trigger: saturated soil during heavy rainfall")

    if not factors:
        factors.append("All monitored conditions within normal range")
    return factors


def _predict_rule_based(features: RiskFeatures) -> RiskResult:
    rainfall_pts = _rainfall_score(features.rainfall_mm_24h)
    soil_pts = _soil_moisture_score(features.soil_moisture_pct)
    slope_pts = _slope_score(features.slope_deg)

    score = rainfall_pts + soil_pts + slope_pts
    if features.rainfall_mm_24h > 100 and features.soil_moisture_pct > 70:
        score = min(score + 8, 100)

    score = round(min(score, 100.0), 1)
    level = _risk_level(score)

    return RiskResult(
        risk_score=score,
        risk_level=level,
        contributing_factors=_contributing_factors(features),
        recommendation=_recommendation(level),
        model_used="rule_based",
    )


def _predict_trained(features: RiskFeatures, model) -> RiskResult:
    import pandas as pd

    row = pd.DataFrame(
        [
            {
                "rainfall_mm_24h": features.rainfall_mm_24h,
                "soil_moisture_pct": features.soil_moisture_pct,
                "slope_deg": features.slope_deg,
                "temperature_c": features.temperature_c if features.temperature_c is not None else 20.0,
            }
        ]
    )[_trained_features]

    probability = model.predict_proba(row)[0][1]
    score = round(float(probability) * 100, 1)
    level = _risk_level(score)

    return RiskResult(
        risk_score=score,
        risk_level=level,
        contributing_factors=_contributing_factors(features),
        recommendation=_recommendation(level),
        model_used="trained",
    )


def predict(features: RiskFeatures) -> RiskResult:
    """Try the trained model first; fall back to the transparent rule-based
    scorer if it isn't available or errors out on this input."""
    model = _load_trained_model()
    if model is not None:
        try:
            return _predict_trained(features, model)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Trained model inference failed (%s); using rule-based fallback.", exc)
    return _predict_rule_based(features)
