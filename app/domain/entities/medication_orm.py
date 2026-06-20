"""Medication ORM Models - from diploma diagram."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class MedicationORM(Base):
    """
    Medication entity - represents a medication in the system.
    
    Attributes:
        id: Primary key
        name: Medication name
        dosage: Dosage amount (e.g., "200 mg" or "1 таблетка")
        unit: Unit of measurement (mg, ml, etc.) (optional)
    """
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(200), nullable=False)
    dosage = Column(String(50), nullable=False)  # e.g., "200 mg" or "1 таблетка"
    unit = Column(String(20), nullable=True)  # mg, ml, tablet, etc. (optional)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    intakes = relationship("MedicationIntakeORM", back_populates="medication", lazy="dynamic",
                          cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<MedicationORM(id={self.id}, {self.name} {self.dosage})>"


class MedicationIntakeORM(Base):
    """
    MedicationIntake entity - records when patient took medication.
    Enhanced version with prescription tracking and scheduling.
    
    Attributes:
        id: Primary key
        medication_id: FK to medications
        prescription_id: FK to prescriptions (the source prescription)
        patient_id: FK to users (denormalized for quick queries)
        measurement_id: FK to measurements (optional context)
        taken_at: When medication was taken
        scheduled_time: When it was scheduled to be taken
        dosage_taken: Actual dosage taken (may differ from prescribed)
        notes: Any notes about this intake
        status: on_time, late, missed, skipped, early
    """
    __tablename__ = "medication_intakes"
    
    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True, index=True)
    
    # Timing
    scheduled_time = Column(DateTime(timezone=True), nullable=True, index=True)  # Запланований час
    taken_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Фактичний час прийому
    
    # Dosage tracking
    dosage_taken = Column(Float, nullable=True)  # Фактична доза
    dosage_unit = Column(String(20), nullable=True)  # мг, мл, таблетки
    
    # Status tracking
    status = Column(String(20), nullable=False, default="pending")  # pending, taken, missed, skipped, late
    
    # Adherence tracking
    taken_on_time = Column(Boolean, nullable=True)  # Чи вчасно прийнято
    minutes_delay = Column(Integer, nullable=True)  # Запізнення в хвилинах (може бути від'ємним - раніше)
    
    # Context
    taken_with_food = Column(Boolean, nullable=True)  # Прийнято з їжею
    notes = Column(Text, nullable=True)  # Нотатки пацієнта
    skip_reason = Column(String(200), nullable=True)  # Причина пропуску (якщо skipped)
    
    # Reminder tracking
    reminder_sent = Column(Boolean, default=False)  # Нагадування відправлено
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    reminder_acknowledged = Column(Boolean, default=False)  # Пацієнт підтвердив
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    medication = relationship("MedicationORM", back_populates="intakes")
    prescription = relationship("PrescriptionORM", back_populates="intakes")
    patient = relationship("UserORM", back_populates="medication_intakes")
    measurement = relationship("MeasurementORM", back_populates="medication_intakes")
    
    def __repr__(self) -> str:
        return f"<MedicationIntakeORM(id={self.id}, med_id={self.medication_id}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "medication_id": self.medication_id,
            "prescription_id": self.prescription_id,
            "patient_id": self.patient_id,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "taken_at": self.taken_at.isoformat() if self.taken_at else None,
            "dosage_taken": self.dosage_taken,
            "status": self.status,
            "taken_on_time": self.taken_on_time,
            "minutes_delay": self.minutes_delay,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def record_intake(self, taken_at: datetime, dosage: float = None, notes: str = None):
        """Record that medication was taken."""
        from datetime import timedelta
        
        self.taken_at = taken_at
        self.status = "taken"
        if dosage:
            self.dosage_taken = dosage
        if notes:
            self.notes = notes
        
        # Calculate if on time
        if self.scheduled_time:
            delay = (taken_at - self.scheduled_time).total_seconds() / 60
            self.minutes_delay = int(delay)
            self.taken_on_time = abs(delay) <= 30  # Within 30 minutes is on time
            if delay > 30:
                self.status = "late"
            elif delay < -30:
                self.status = "early"
    
    def mark_missed(self):
        """Mark as missed."""
        self.status = "missed"
    
    def mark_skipped(self, reason: str = None):
        """Mark as intentionally skipped."""
        self.status = "skipped"
        if reason:
            self.skip_reason = reason
