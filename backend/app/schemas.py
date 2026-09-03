from typing import Optional
from pydantic import BaseModel, Field


class ReadingInput(BaseModel):
    rainfall_mm_24h: float = Field(..., ge=0, description="Rainfall in the last 24 hours, mm")
    soil_moisture_pct: float = Field(..., ge=0, le=100, description="Soil moisture, percent")
    slope_deg: float = Field(..., ge=0, le=90, description="Slope angle, degrees")
    temperature_c: Optional[float] = Field(None, description="Ambient temperature, Celsius")


class RiskAssessment(BaseModel):
    risk_score: float
    risk_level: str
    contributing_factors: list[str]
    recommendation: str


class LocationReading(ReadingInput):
    location_id: str
    location_name: str
    state: str
    lat: float
    lon: float
    risk_score: float
    risk_level: str
    contributing_factors: list[str]
    recommendation: str
