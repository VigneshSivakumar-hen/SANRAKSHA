from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas import (
    HistoryEntry,
    IngestPayload,
    LocationReading,
    ReadingInput,
    RiskAssessment,
    SyncResult,
)
from app.services import prediction_service

router = APIRouter(prefix="/api", tags=["prediction"])


@router.get("/dashboard", response_model=list[LocationReading])
def get_dashboard(db: Session = Depends(get_db)):
    """Latest reading + risk assessment for every registered location."""
    return prediction_service.get_dashboard_readings(db)


@router.get("/locations/{location_id}/history", response_model=list[HistoryEntry])
def get_history(location_id: str, db: Session = Depends(get_db)):
    """Recent readings + predictions for one location, most recent first."""
    return prediction_service.get_location_history(db, location_id)


@router.post("/predict", response_model=RiskAssessment)
def predict_risk(reading: ReadingInput):
    """Run the risk model against a single manually-entered reading (not persisted)."""
    return prediction_service.assess_custom_reading(reading.model_dump())


@router.post("/sync/run", response_model=list[SyncResult])
def run_sync(db: Session = Depends(get_db)):
    """Manually trigger an IMD + satellite data pull for every location.
    In production this is what the background scheduler calls on an interval."""
    return prediction_service.sync_all_locations(db)


@router.post("/ingest")
def ingest_reading(payload: IngestPayload, db: Session = Depends(get_db)):
    """Endpoint the IoT gateway posts sensor readings to."""
    if payload.token != settings.INGEST_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid ingest token")
    try:
        return prediction_service.ingest_sensor_reading(
            db,
            location_id=payload.location_id,
            rainfall_mm_24h=payload.rainfall_mm_24h,
            soil_moisture_pct=payload.soil_moisture_pct,
            temperature_c=payload.temperature_c,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
