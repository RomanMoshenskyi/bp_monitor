"""Measurement ORM Model - BloodPressureMeasurement from diploma."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class MeasurementORM(Base):
    """
    BloodPressureMeasurement entity from diploma diagram.
    
    Attributes:
        id: Primary key
        user_id: FK to users (patient)
        systolic: Systolic pressure (mmHg)
        diastolic: Diastolic pressure (mmHg)
        pulse: Heart rate (bpm)
        measured_at: Timestamp of measurement
        latitude: Optional GPS latitude
        longitude: Optional GPS longitude
        notes: Optional text notes
        weather_snapshot_id: FK to weather_snapshots
    """
    __tablename__ = "measurements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Blood pressure values
    systolic = Column(Integer, nullable=False)
    diastolic = Column(Integer, nullable=False)
    pulse = Column(Integer, nullable=True)
    
    # When measurement was taken
    measured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Optional geolocation
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Optional notes
    notes = Column(Text, nullable=True)
    
    # Foreign key to weather snapshot (can be null if weather unavailable)
    weather_snapshot_id = Column(Integer, ForeignKey("weather_snapshots.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("UserORM", back_populates="measurements")
    weather_snapshot = relationship("WeatherSnapshotORM", back_populates="measurements")
    recommendations = relationship("RecommendationORM", back_populates="measurement", lazy="dynamic")
    medication_intakes = relationship("MedicationIntakeORM", back_populates="measurement", lazy="dynamic")
    activities = relationship("ActivityEventORM", back_populates="measurement", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<MeasurementORM(id={self.id}, user_id={self.user_id}, {self.systolic}/{self.diastolic})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "systolic": self.systolic,
            "diastolic": self.diastolic,
            "pulse": self.pulse,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "notes": self.notes,
            "weather_snapshot_id": self.weather_snapshot_id,
        }
