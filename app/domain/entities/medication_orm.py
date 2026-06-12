"""Medication ORM Models - from diploma diagram."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class MedicationORM(Base):
    """
    Medication entity - represents a medication a patient takes.
    
    Attributes:
        id: Primary key
        patient_id: FK to users
        name: Medication name
        dosage: Dosage amount (e.g., 10.0)
        unit: Unit of measurement (mg, ml, etc.)
        frequency: How often to take (e.g., "twice daily")
        notes: Additional notes
    """
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    dosage = Column(Float, nullable=False)  # e.g., 10.0
    unit = Column(String(20), nullable=False)  # mg, ml, tablet, etc.
    frequency = Column(String(100), nullable=True)  # e.g., "twice daily"
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("UserORM", back_populates="medications")
    intakes = relationship("MedicationIntakeORM", back_populates="medication", lazy="dynamic",
                          cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<MedicationORM(id={self.id}, patient_id={self.patient_id}, {self.name} {self.dosage}{self.unit})>"


class MedicationIntakeORM(Base):
    """
    MedicationIntake entity - records when patient took medication.
    Linked to specific measurement for context.
    
    Attributes:
        id: Primary key
        medication_id: FK to medications
        patient_id: FK to users (denormalized for quick queries)
        measurement_id: FK to measurements (optional context)
        taken_at: When medication was taken
        dosage_taken: Actual dosage taken (may differ from prescribed)
        notes: Any notes about this intake
    """
    __tablename__ = "medication_intakes"
    
    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True, index=True)
    
    taken_at = Column(DateTime(timezone=True), nullable=False, index=True)
    dosage_taken = Column(Float, nullable=True)  # Actual amount taken
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    medication = relationship("MedicationORM", back_populates="intakes")
    patient = relationship("UserORM", back_populates="medication_intakes")
    measurement = relationship("MeasurementORM", back_populates="medication_intakes")
    
    def __repr__(self) -> str:
        return f"<MedicationIntakeORM(id={self.id}, med_id={self.medication_id}, taken_at={self.taken_at})>"
