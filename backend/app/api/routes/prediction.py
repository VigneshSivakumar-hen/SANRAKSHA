from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response
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
    SatelliteLatestResponse,
    SatelliteObservation,
    SyncResult,
)
from app.services import prediction_service, satellite_imagery_service

router = APIRouter(prefix="/api", tags=["prediction"])


def require_admin_key(x_admin_key: str = Header(default="")) -> None:
    """Guard for privileged endpoints (manual sync)."""
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
    """Run the risk model against a single manually-entered reading."""
    return prediction_service.assess_custom_reading(reading.model_dump())


@router.post(
    "/sync/run",
    response_model=list[SyncResult],
    dependencies=[Depends(require_admin_key)],
)
@limiter.limit("5/hour")
def run_sync(request: Request, db: Session = Depends(get_db)):
    """Manually trigger the environmental-data synchronization."""
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


@router.get(
    "/satellite/latest/{location_id}",
    response_model=SatelliteLatestResponse,
)
@limiter.limit("12/minute")
def get_satellite_latest(
    request: Request,
    location_id: str,
    db: Session = Depends(get_db),
):
    """Return the latest available Sentinel-1 and Sentinel-2 observations."""
    from app.models import Location

    location = db.query(Location).filter(Location.id == location_id).first()
    if location is None:
        raise HTTPException(status_code=404, detail="Unknown location_id")

    try:
        observations, preferred = satellite_imagery_service.get_latest_for_location(
            location.lat,
            location.lon,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "location_id": location.id,
        "location_name": location.name,
        "lat": location.lat,
        "lon": location.lon,
        "preferred_collection": preferred,
        "observations": [
            SatelliteObservation.model_validate(item)
            for item in observations
        ],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/satellite/image/{location_id}")
@limiter.limit("6/minute")
def get_satellite_image(
    request: Request,
    location_id: str,
    collection: str,
    acquired_at: str,
    db: Session = Depends(get_db),
):
    """Proxy a real Sentinel acquisition through the SANRAKSHA backend.

    Copernicus credentials remain server-side; the browser only receives
    rendered image bytes.
    """
    from app.models import Location

    location = db.query(Location).filter(Location.id == location_id).first()
    if location is None:
        raise HTTPException(status_code=404, detail="Unknown location_id")

    try:
        image = satellite_imagery_service.render_observation(
            location.lat,
            location.lon,
            collection,
            acquired_at,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return Response(
        content=image,
        media_type="image/png" if collection == "sentinel-2-l2a" else "image/jpeg",
        headers={"Cache-Control": "public, max-age=600"},
    )
