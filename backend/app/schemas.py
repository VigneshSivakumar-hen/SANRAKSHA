from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReadingInput(BaseModel):
    rainfall_mm_24h: float = Field(..., ge=0, description="Rainfall in the last 24 hours, mm")
    soil_moisture_pct: float = Field(..., ge=0, le=100, description="Soil moisture, percent")
    slope_deg: float = Field(..., ge=0, le=90, description="Slope angle, degrees")
    temperature_c: Optional[float] = Field(None, description="Ambient temperature, Celsius")


class RiskAssessment(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    risk_score: float
    risk_level: str
    model_used: str
    contributing_factors: list[str]
    recommendation: str


class LocationReading(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    location_id: str
    location_name: str
    state: str
    lat: float
    lon: float
    slope_deg: float
    rainfall_mm_24h: Optional[float]
    soil_moisture_pct: Optional[float]
    temperature_c: Optional[float]
    risk_score: float
    risk_level: str
    model_used: str
    contributing_factors: list[str]
    recommendation: str
    updated_at: str


class HistoryEntry(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    risk_score: float
    risk_level: str
    model_used: str
    rainfall_mm_24h: Optional[float]
    soil_moisture_pct: Optional[float]
    source: Optional[str]
    recorded_at: str


class IngestPayload(BaseModel):
    """Payload the IoT gateway posts for each sensor reading."""
    location_id: str
    rainfall_mm_24h: float = Field(..., ge=0)
    soil_moisture_pct: float = Field(..., ge=0, le=100)
    temperature_c: Optional[float] = None
    token: str = Field(..., description="Shared ingest token, see INGEST_TOKEN setting")


class SyncResult(BaseModel):
    location_id: str
    risk_level: str
