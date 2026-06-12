"""Activity ORM Model - ActivityEvent from diploma diagram."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.infrastructure.orm.base import Base


class ActivityType(str, enum.Enum):
    """Types of physical activity."""
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    GYM = "gym"
    YOGA = "yoga"
    SPORT = "sport"
    OTHER = "other"


class ActivityEventORM(Base):
    """
    ActivityEvent entity - records physical activity.
    Linked to measurement for BP/activity correlation analysis.
    
    Attributes:
        id: Primary key
        patient_id: FK to users
        measurement_id: FK to measurements (optional context)
        activity_type: Type of activity (enum)
        duration_minutes: How long the activity lasted
        intensity: Low/medium/high
        calories_burned: Optional calorie estimate
        started_at: When activity started
        notes: Additional details
    """
    __tablename__ = "activity_events"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True, index=True)
    
    activity_type = Column(Enum(ActivityType), nullable=False)
    duration_minutes = Column(Integer, nullable=False)  # Duration in minutes
    intensity = Column(String(20), nullable=True)  # low, medium, high
    calories_burned = Column(Integer, nullable=True)  # Optional
    
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("UserORM", back_populates="activities")
    measurement = relationship("MeasurementORM", back_populates="activities")
    
    def __repr__(self) -> str:
        return f"<ActivityEventORM(id={self.id}, patient_id={self.patient_id}, {self.activity_type.value}, {self.duration_minutes}min)>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "measurement_id": self.measurement_id,
            "activity_type": self.activity_type.value if self.activity_type else None,
            "duration_minutes": self.duration_minutes,
            "intensity": self.intensity,
            "calories_burned": self.calories_burned,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "notes": self.notes,
        }
