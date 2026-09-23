import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from sqlalchemy import func
from pathlib import Path

from sqlalchemy.orm import Session

from app.ml.predictor import RiskFeatures, predict, predict_batch
from app.models import Location, Prediction, Reading
from app.services import imd_service, satellite_service

logger = logging.getLogger(__name__)

SAMPLE_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "sample" / "sample_readings.json"


def _load_sample_locations() -> list[dict]:
    if not SAMPLE_DATA_PATH.exists():
        return []
    with open(SAMPLE_DATA_PATH, "r") as f:
        return json.load(f)


def _run_and_store(db: Session, location: Location, rainfall_mm_24h: float,
                    soil_moisture_pct: float, temperature_c: float | None, source: str) -> Prediction:
    reading = Reading(
        location_id=location.id,
        source=source,
        rainfall_mm_24h=rainfall_mm_24h,
        soil_moisture_pct=soil_moisture_pct,
        temperature_c=temperature_c,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(reading)
    db.flush()  # get reading.id without committing yet

    risk = predict(
        RiskFeatures(
            rainfall_mm_24h=rainfall_mm_24h,
            soil_moisture_pct=soil_moisture_pct,
            slope_deg=location.slope_deg,
            temperature_c=temperature_c,
        )
    )

    prediction = Prediction(
        location_id=location.id,
        reading_id=reading.id,
        risk_score=risk.risk_score,
        risk_level=risk.risk_level,
        model_used=risk.model_used,
        contributing_factors=json.dumps(risk.contributing_factors),
        recommendation=risk.recommendation,
        created_at=datetime.now(timezone.utc),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def seed_if_empty(db: Session) -> None:
    """First-run bootstrap: register the sample locations and give each one
    an initial reading + prediction, so the dashboard isn't empty before
    the first sync or IoT message arrives."""
    if db.query(Location).count() > 0:
        return

    for entry in _load_sample_locations():
        location = Location(
            id=entry["location_id"],
            name=entry["location_name"],
            state=entry["state"],
            lat=entry["lat"],
            lon=entry["lon"],
            slope_deg=entry["slope_deg"],
            imd_district_id=entry.get("imd_district_id"),
        )
        db.add(location)
        db.flush()
        _run_and_store(
            db,
            location,
            rainfall_mm_24h=entry["rainfall_mm_24h"],
            soil_moisture_pct=entry["soil_moisture_pct"],
            temperature_c=entry.get("temperature_c"),
            source="seed",
        )


def _fetch_environment(location: Location):
    """Fetch external environmental data for one location.

    This helper does not touch SQLAlchemy, so it is safe to run in worker
    threads while the database session remains on the caller thread.
    """
    rainfall = imd_service.get_latest_rainfall(
        location.lat, location.lon, location.imd_district_id
    )
    soil_moisture = satellite_service.get_latest_soil_moisture(
        location.lat, location.lon
    )
    return location, rainfall, soil_moisture


def sync_all_locations(db: Session) -> list[dict]:
    """Fetch environmental data concurrently, then infer/store results."""
    locations = db.query(Location).all()
    if not locations:
        return []

    worker_count = min(settings.SYNC_FETCH_WORKERS, len(locations))
    logger.info(
        "Starting environmental sync for %d locations using %d workers.",
        len(locations),
        worker_count,
    )

    # Only network-bound provider calls run in worker threads. The SQLAlchemy
    # Session is never shared with worker threads.
    with ThreadPoolExecutor(
        max_workers=worker_count,
        thread_name_prefix="sanraksha-sync",
    ) as executor:
        futures = [
            executor.submit(_fetch_environment, location)
            for location in locations
        ]
        # Preserve location order so prediction results map deterministically.
        fetched = [future.result() for future in futures]

    features = [
        RiskFeatures(
            rainfall_mm_24h=rainfall.rainfall_mm_24h,
            soil_moisture_pct=soil_moisture,
            slope_deg=location.slope_deg,
            temperature_c=rainfall.temperature_c,
        )
        for location, rainfall, soil_moisture in fetched
    ]

    predictions = predict_batch(features)
    results = []

    # Database writes remain sequential and use the existing transaction.
    for (location, rainfall, soil_moisture), risk in zip(fetched, predictions):
        reading = Reading(
            location_id=location.id,
            source="sync",
            rainfall_mm_24h=rainfall.rainfall_mm_24h,
            soil_moisture_pct=soil_moisture,
            temperature_c=rainfall.temperature_c,
            recorded_at=datetime.now(timezone.utc),
        )
        db.add(reading)
        db.flush()

        prediction = Prediction(
            location_id=location.id,
            reading_id=reading.id,
            risk_score=risk.risk_score,
            risk_level=risk.risk_level,
            model_used=risk.model_used,
            contributing_factors=json.dumps(risk.contributing_factors),
            recommendation=risk.recommendation,
            created_at=datetime.now(timezone.utc),
        )
        db.add(prediction)
        results.append({"location_id": location.id, "risk_level": prediction.risk_level})

    db.commit()
    logger.info("Environmental sync completed for %d locations.", len(results))
    return results


def ingest_sensor_reading(db: Session, location_id: str, rainfall_mm_24h: float,
                           soil_moisture_pct: float, temperature_c: float | None) -> dict:
    """Store a reading pushed by the IoT gateway and run the predictor
    against it immediately."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if location is None:
        raise ValueError(f"Unknown location_id: {location_id}")

    prediction = _run_and_store(
        db, location, rainfall_mm_24h, soil_moisture_pct, temperature_c, source="iot"
    )
    return {
        "location_id": location_id,
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level,
        "model_used": prediction.model_used,
    }


def get_dashboard_readings(db: Session) -> list[dict]:
    """Latest reading + prediction for every location using one query."""
    latest_prediction_ids = (
        db.query(
            Prediction.location_id,
            func.max(Prediction.id).label("prediction_id"),
        )
        .group_by(Prediction.location_id)
        .subquery()
    )

    rows = (
        db.query(Location, Prediction, Reading)
        .join(
            latest_prediction_ids,
            latest_prediction_ids.c.location_id == Location.id,
        )
        .join(
            Prediction,
            Prediction.id == latest_prediction_ids.c.prediction_id,
        )
        .outerjoin(
            Reading,
            Reading.id == Prediction.reading_id,
        )
        .all()
    )

    return [
        {
            "location_id": location.id,
            "location_name": location.name,
            "state": location.state,
            "lat": location.lat,
            "lon": location.lon,
            "slope_deg": location.slope_deg,
            "rainfall_mm_24h": reading.rainfall_mm_24h if reading else None,
            "soil_moisture_pct": reading.soil_moisture_pct if reading else None,
            "temperature_c": reading.temperature_c if reading else None,
            "risk_score": prediction.risk_score,
            "risk_level": prediction.risk_level,
            "model_used": prediction.model_used,
            "contributing_factors": json.loads(prediction.contributing_factors),
            "recommendation": prediction.recommendation,
            "updated_at": prediction.created_at.isoformat(),
        }
        for location, prediction, reading in rows
    ]


def get_location_history(db: Session, location_id: str, limit: int = 50) -> list[dict]:
    predictions = (
        db.query(Prediction)
        .filter(Prediction.location_id == location_id)
        .order_by(Prediction.created_at.desc())
        .limit(limit)
        .all()
    )
    history = []
    for p in predictions:
        reading = db.query(Reading).filter(Reading.id == p.reading_id).first()
        history.append(
            {
                "risk_score": p.risk_score,
                "risk_level": p.risk_level,
                "model_used": p.model_used,
                "rainfall_mm_24h": reading.rainfall_mm_24h if reading else None,
                "soil_moisture_pct": reading.soil_moisture_pct if reading else None,
                "source": reading.source if reading else None,
                "recorded_at": p.created_at.isoformat(),
            }
        )
    return history


def assess_custom_reading(payload: dict) -> dict:
    """Run the predictor against a caller-supplied reading without persisting it
    (used by the dashboard's manual 'test a reading' form)."""
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
        "model_used": risk.model_used,
        "contributing_factors": risk.contributing_factors,
        "recommendation": risk.recommendation,
    }
