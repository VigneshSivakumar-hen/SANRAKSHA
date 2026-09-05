from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
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


def require_admin_key(x_admin_key: str = Header(default="")) -> None:
    """Guard for privileged endpoints (manual sync). If ADMIN_API_KEY isn't
    set, the check is skipped — convenient for local dev, but always set
    it in any public deployment."""
    if settings.ADMIN_API_KEY and x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-Admin-Key header")


@router.get("/dashboard", response_model=list[LocationReading])
def get_dashboard(db: Session = Depends(get_db)):
    """Latest reading + risk assessment for every registered location."""
    return prediction_service.get_dashboard_readings(db)


@router.get("/locations/{location_id}/history", response_model=list[HistoryEntry])
def get_history(location_id: str, db: Session = Depends(get_db)):
    """Recent readings + predictions for one location, most recent first."""
    return prediction_service.get_location_history(db, location_id)


@router.post("/predict", response_model=RiskAssessment)
@limiter.limit("20/minute")
def predict_risk(request: Request, reading: ReadingInput):
    """Run the risk model against a single manually-entered reading (not persisted).
    Public demo endpoint — rate-limited per IP to prevent abuse."""
    return prediction_service.assess_custom_reading(reading.model_dump())


@router.post("/sync/run", response_model=list[SyncResult], dependencies=[Depends(require_admin_key)])
@limiter.limit("5/hour")
def run_sync(request: Request, db: Session = Depends(get_db)):
    """Manually trigger an IMD + satellite data pull for every location.
    In production this is what the background scheduler calls on an interval.
    Privileged: requires the X-Admin-Key header when ADMIN_API_KEY is set,
    since each call fans out to external data sources."""
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
