from fastapi import APIRouter

from app.schemas import ReadingInput, RiskAssessment, LocationReading
from app.services import prediction_service

router = APIRouter(prefix="/api", tags=["prediction"])


@router.get("/dashboard", response_model=list[LocationReading])
def get_dashboard():
    """All sample monitoring locations with a live risk assessment for each."""
    return prediction_service.get_dashboard_readings()


@router.post("/predict", response_model=RiskAssessment)
def predict_risk(reading: ReadingInput):
    """Run the risk model against a single manually-entered or sensor-submitted reading."""
    return prediction_service.assess_custom_reading(reading.model_dump())
