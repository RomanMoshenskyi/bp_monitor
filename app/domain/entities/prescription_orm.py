"""Prescription ORM Model - Doctor prescriptions for patients."""
from __future__ import annotations

from datetime import datetime, date, time
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean, Time, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class PrescriptionStatus(str):
    """Prescription status values."""
    ACTIVE = "active"  # Активний рецепт
    COMPLETED = "completed"  # Завершено (курс прийому закінчено)
    CANCELLED = "cancelled"  # Скасовано лікарем
    EXPIRED = "expired"  # Прострочено


class PrescriptionORM(Base):
    """
    Prescription entity - doctor's prescription for medication.
    
    Links doctor -> patient with specific medication details.
    Contains dosage, frequency, duration, and special instructions.
    When created, generates notification for patient.
    """
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Prescription identification
    prescription_number = Column(String(50), nullable=False, unique=True)
    prescription_date = Column(Date, nullable=False, default=date.today)
    
    # Medication details
    medication_name = Column(String(200), nullable=False)  # Назва ліків
    medication_form = Column(String(100), nullable=True)  # Форма (таблетки, капсули, сироп...)
    dosage = Column(String(100), nullable=False)  # Дозування ("10 мг", "1 таблетка")
    
    # Administration schedule
    frequency_per_day = Column(Integer, nullable=False, default=1)  # Кількість разів на день
    specific_times = Column(ARRAY(Time), nullable=True)  # Конкретні часи прийому ["08:00", "14:00", "20:00"]
    
    # Duration
    duration_days = Column(Integer, nullable=True)  # Тривалість курсу в днях
    start_date = Column(Date, nullable=False, default=date.today)
    end_date = Column(Date, nullable=True)  # Розраховується автоматично
    
    # Administration details
    take_with_food = Column(Boolean, nullable=True)  # Приймати з їжею
    take_before_food = Column(Boolean, nullable=True)  # Приймати до їди
    take_after_food = Column(Boolean, nullable=True)  # Приймати після їди
    special_instructions = Column(Text, nullable=True)  # Особливі інструкції
    
    # Doctor's notes
    prescribed_for = Column(Text, nullable=True)  # Для чого призначено (показання)
    contraindications = Column(Text, nullable=True)  # Протипоказання
    side_effects_notes = Column(Text, nullable=True)  # Можливі побічні ефекти
    interactions_warning = Column(Text, nullable=True)  # Взаємодія з іншими ліками
    
    # Status
    status = Column(String(20), nullable=False, default=PrescriptionStatus.ACTIVE)
    
    # Notification tracking
    patient_notified = Column(Boolean, default=False)  # Пацієнт отримав сповіщення
    notification_seen_at = Column(DateTime, nullable=True)  # Коли пацієнт переглянув
    notification_accepted = Column(Boolean, nullable=True)  # Пацієнт прийняв рецепт
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cancelled_at = Column(DateTime, nullable=True)  # Коли скасовано
    cancelled_reason = Column(Text, nullable=True)  # Причина скасування
    
    # Relationships
    doctor = relationship("UserORM", foreign_keys=[doctor_id], back_populates="prescriptions_created")
    patient = relationship("UserORM", foreign_keys=[patient_id], back_populates="prescriptions_received")
    intakes = relationship("MedicationIntakeORM", back_populates="prescription", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<PrescriptionORM(id={self.id}, number={self.prescription_number}, med={self.medication_name})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "prescription_number": self.prescription_number,
            "doctor_id": self.doctor_id,
            "patient_id": self.patient_id,
            "prescription_date": self.prescription_date.isoformat() if self.prescription_date else None,
            "medication_name": self.medication_name,
            "medication_form": self.medication_form,
            "dosage": self.dosage,
            "frequency_per_day": self.frequency_per_day,
            "specific_times": [t.isoformat() for t in self.specific_times] if self.specific_times else None,
            "duration_days": self.duration_days,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "take_with_food": self.take_with_food,
            "special_instructions": self.special_instructions,
            "prescribed_for": self.prescribed_for,
            "status": self.status,
            "patient_notified": self.patient_notified,
            "notification_seen_at": self.notification_seen_at.isoformat() if self.notification_seen_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def cancel(self, reason: str = None):
        """Cancel the prescription."""
        self.status = PrescriptionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.cancelled_reason = reason
    
    def mark_completed(self):
        """Mark prescription as completed."""
        self.status = PrescriptionStatus.COMPLETED
    
    def calculate_end_date(self):
        """Calculate end date based on duration."""
        if self.duration_days and self.start_date:
            from datetime import timedelta
            self.end_date = self.start_date + timedelta(days=self.duration_days)
