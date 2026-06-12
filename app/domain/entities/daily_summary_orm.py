"""DailySummary ORM Model - aggregated daily stats from diploma."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class DailySummaryORM(Base):
    """
    DailySummary entity - aggregated statistics per patient per day.
    
    From diploma: aggregates measurements for quick dashboard display.
    
    Attributes:
        id: Primary key
        patient_id: FK to users
        summary_date: Date of summary (unique per patient)
        
        Systolic stats:
        - avg_systolic: Average systolic BP
        - min_systolic, max_systolic: Min/max values
        
        Diastolic stats:
        - avg_diastolic: Average diastolic BP
        - min_diastolic, max_diastolic: Min/max values
        
        Pulse stats:
        - avg_pulse: Average pulse
        
        measurements_count: How many measurements contributed
    """
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    summary_date = Column(Date, nullable=False, index=True)
    
    # Systolic statistics
    avg_systolic = Column(Float, nullable=True)
    min_systolic = Column(Integer, nullable=True)
    max_systolic = Column(Integer, nullable=True)
    
    # Diastolic statistics
    avg_diastolic = Column(Float, nullable=True)
    min_diastolic = Column(Integer, nullable=True)
    max_diastolic = Column(Integer, nullable=True)
    
    # Pulse statistics
    avg_pulse = Column(Float, nullable=True)
    min_pulse = Column(Integer, nullable=True)
    max_pulse = Column(Integer, nullable=True)
    
    # Count
    measurements_count = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('patient_id', 'summary_date', name='uq_daily_summary_patient_date'),
        Index('ix_daily_summary_patient_date', 'patient_id', 'summary_date'),
    )
    
    # Relationships
    patient = relationship("UserORM", back_populates="daily_summaries")
    
    def __repr__(self) -> str:
        return f"<DailySummaryORM(id={self.id}, patient_id={self.patient_id}, date={self.summary_date}, count={self.measurements_count})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "summary_date": self.summary_date.isoformat() if self.summary_date else None,
            "systolic": {
                "avg": self.avg_systolic,
                "min": self.min_systolic,
                "max": self.max_systolic,
            },
            "diastolic": {
                "avg": self.avg_diastolic,
                "min": self.min_diastolic,
                "max": self.max_diastolic,
            },
            "pulse": {
                "avg": self.avg_pulse,
                "min": self.min_pulse,
                "max": self.max_pulse,
            },
            "measurements_count": self.measurements_count,
        }
