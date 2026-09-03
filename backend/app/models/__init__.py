from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Location(Base):
    """A monitored site. Slope is static (surveyed once); everything else
    that changes over time lives in Reading rows linked to it."""

    __tablename__ = "locations"

    id = Column(String, primary_key=True)  # e.g. "munnar-01"
    name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    slope_deg = Column(Float, nullable=False)

    readings = relationship("Reading", back_populates="location", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="location", cascade="all, delete-orphan")


class Reading(Base):
    """One rainfall/soil-moisture/temperature observation for a location,
    from any source (IMD sync, IoT gateway, or manual entry)."""

    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=False)
    source = Column(String, nullable=False)  # "imd" | "iot" | "manual"
    rainfall_mm_24h = Column(Float, nullable=False)
    soil_moisture_pct = Column(Float, nullable=False)
    temperature_c = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    location = relationship("Location", back_populates="readings")


class Prediction(Base):
    """A risk assessment computed from a Reading + the location's slope."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=False)
    reading_id = Column(Integer, ForeignKey("readings.id"), nullable=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    model_used = Column(String, nullable=False)  # "trained" | "rule_based"
    contributing_factors = Column(String, nullable=False)  # JSON-encoded list
    recommendation = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    location = relationship("Location", back_populates="predictions")
