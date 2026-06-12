"""Recommendation ORM Model - from diploma class diagram."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.infrastructure.orm.base import Base


class SeverityLevel(str, enum.Enum):
    """Recommendation severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationORM(Base):
    """
    Recommendation entity - from diploma class diagram.
    
    System-generated recommendations based on analysis.
    
    Attributes:
        id: Primary key
        patient_id: FK to users (recipient)
        measurement_id: FK to measurements (optional context)
        severity: low/medium/high/critical
        message: Human-readable recommendation text
        category: Type of recommendation (diet, exercise, medical, etc.)
        is_read: Whether patient has seen this
        is_acknowledged: Whether patient acknowledged it
    """
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True, index=True)
    
    severity = Column(Enum(SeverityLevel), nullable=False, default=SeverityLevel.LOW)
    category = Column(String(50), nullable=True)  # diet, exercise, medical, lifestyle
    message = Column(Text, nullable=False)
    
    # Tracking
    is_read = Column(String(1), default="N")  # Y/N
    is_acknowledged = Column(String(1), default="N")  # Y/N
    read_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("UserORM", back_populates="recommendations")
    measurement = relationship("MeasurementORM", back_populates="recommendations")
    
    def __repr__(self) -> str:
        return f"<RecommendationORM(id={self.id}, patient_id={self.patient_id}, severity={self.severity.value}, read={self.is_read})>"
    
    def mark_as_read(self) -> None:
        """Mark recommendation as read."""
        self.is_read = "Y"
        self.read_at = datetime.utcnow()
    
    def acknowledge(self) -> None:
        """Patient acknowledges the recommendation."""
        self.is_acknowledged = "Y"
        self.acknowledged_at = datetime.utcnow()
        if self.is_read == "N":
            self.mark_as_read()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "measurement_id": self.measurement_id,
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "is_read": self.is_read == "Y",
            "is_acknowledged": self.is_acknowledged == "Y",
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
