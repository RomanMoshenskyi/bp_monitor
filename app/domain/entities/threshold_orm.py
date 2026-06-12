"""Threshold ORM Model - ThresholdProfile from diploma diagram."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class ThresholdProfileORM(Base):
    """
    ThresholdProfile entity - personalized BP thresholds for a patient.
    
    From diploma diagram:
    - sysMin, sysMax: Systolic thresholds
    - diaMin, diaMax: Diastolic thresholds
    
    Attributes:
        id: Primary key
        patient_id: FK to users (one-to-one relationship)
        sys_min, sys_max: Systolic min/max
        dia_min, dia_max: Diastolic min/max
        pulse_min, pulse_max: Optional pulse thresholds
        is_default: Whether this is system default profile
        is_active: Whether this profile is currently active
    """
    __tablename__ = "threshold_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True, index=True)
    
    # Blood pressure thresholds (mmHg)
    sys_min = Column(Integer, nullable=False, default=90)
    sys_max = Column(Integer, nullable=False, default=140)
    dia_min = Column(Integer, nullable=False, default=60)
    dia_max = Column(Integer, nullable=False, default=90)
    
    # Optional pulse thresholds (bpm)
    pulse_min = Column(Integer, nullable=True)
    pulse_max = Column(Integer, nullable=True)
    
    # Profile flags
    is_default = Column(Boolean, default=False)  # System-wide default
    is_active = Column(Boolean, default=True)  # Currently active for patient
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("UserORM", back_populates="threshold_profile")
    
    def __repr__(self) -> str:
        return f"<ThresholdProfileORM(id={self.id}, patient_id={self.patient_id}, sys:{self.sys_min}-{self.sys_max}, dia:{self.dia_min}-{self.dia_max})>"
    
    def check_measurement(self, systolic: int, diastolic: int, pulse: int = None) -> dict:
        """
        Check if measurement is within thresholds.
        Returns status dict with warnings.
        """
        result = {
            "systolic_status": "normal",
            "diastolic_status": "normal",
            "pulse_status": "normal" if pulse is None else "unknown",
            "overall_status": "normal",
            "warnings": []
        }
        
        # Check systolic
        if systolic < self.sys_min:
            result["systolic_status"] = "low"
            result["warnings"].append(f"Systolic too low: {systolic} < {self.sys_min}")
        elif systolic > self.sys_max:
            result["systolic_status"] = "high"
            result["warnings"].append(f"Systolic too high: {systolic} > {self.sys_max}")
        
        # Check diastolic
        if diastolic < self.dia_min:
            result["diastolic_status"] = "low"
            result["warnings"].append(f"Diastolic too low: {diastolic} < {self.dia_min}")
        elif diastolic > self.dia_max:
            result["diastolic_status"] = "high"
            result["warnings"].append(f"Diastolic too high: {diastolic} > {self.dia_max}")
        
        # Check pulse if thresholds set
        if pulse is not None and self.pulse_min is not None and self.pulse_max is not None:
            if pulse < self.pulse_min:
                result["pulse_status"] = "low"
                result["warnings"].append(f"Pulse too low: {pulse} < {self.pulse_min}")
            elif pulse > self.pulse_max:
                result["pulse_status"] = "high"
                result["warnings"].append(f"Pulse too high: {pulse} > {self.pulse_max}")
        
        # Overall status
        if result["warnings"]:
            result["overall_status"] = "warning"
        
        return result
