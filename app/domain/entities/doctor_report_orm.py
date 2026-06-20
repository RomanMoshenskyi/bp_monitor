"""Doctor Report ORM Model - Medical reports created by doctors."""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class DoctorReportORM(Base):
    """
    Doctor Medical Report entity - professional medical reports created by doctors.
    
    These are official medical documents that doctors fill out for patients,
    containing diagnosis, complaints, examination results, prescriptions,
    and doctor's signature.
    
    Reports are private to the doctor who created them (doctor_id).
    """
    __tablename__ = "doctor_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Patient and Doctor references
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Report identification
    report_number = Column(String(50), nullable=False, unique=True)
    report_date = Column(Date, nullable=False, default=date.today)
    
    # Patient complaints and history
    chief_complaint = Column(Text, nullable=True)  # Головні скарги
    history_illness = Column(Text, nullable=True)  # Анамнез захворювання
    history_life = Column(Text, nullable=True)  # Анамнез життя
    
    # Objective examination
    objective_exam = Column(Text, nullable=True)  # Об'єктивний стан
    general_condition = Column(String(100), nullable=True)  # Загальний стан
    consciousness = Column(String(50), nullable=True)  # Свідомість
    body_temperature = Column(String(10), nullable=True)  # Температура тіла
    skin_condition = Column(String(200), nullable=True)  # Стан шкіри
    
    # Vital signs at examination
    heart_rate = Column(Integer, nullable=True)  # ЧСС
    respiratory_rate = Column(Integer, nullable=True)  # ЧДД
    blood_pressure_sys = Column(Integer, nullable=True)  # АТ систолічне
    blood_pressure_dia = Column(Integer, nullable=True)  # АТ діастолічне
    
    # Cardiovascular system
    heart_sounds = Column(String(200), nullable=True)  # Тони серця
    pulse_rhythm = Column(String(50), nullable=True)  # Ритм пульсу
    pulse_character = Column(String(100), nullable=True)  # Характер пульсу
    
    # Diagnosis
    preliminary_diagnosis = Column(Text, nullable=True)  # Попередній діагноз
    final_diagnosis = Column(Text, nullable=True)  # Заключний діагноз
    diagnosis_code_icd = Column(String(20), nullable=True)  # Код МКХ-10
    
    # Examination results
    ecg_results = Column(Text, nullable=True)  # Результати ЕКГ
    xray_results = Column(Text, nullable=True)  # Результати рентгену
    lab_results = Column(Text, nullable=True)  # Лабораторні дані
    other_exams = Column(Text, nullable=True)  # Інші обстеження
    
    # Treatment and recommendations
    treatment_plan = Column(Text, nullable=True)  # План лікування
    prescriptions = Column(Text, nullable=True)  # Призначення (ліки)
    procedures = Column(Text, nullable=True)  # Процедури
    lifestyle_recommendations = Column(Text, nullable=True)  # Рекомендації щодо способу життя
    diet_recommendations = Column(Text, nullable=True)  # Дієтичні рекомендації
    activity_recommendations = Column(Text, nullable=True)  # Рекомендації щодо активності
    
    # Doctor's conclusions
    doctor_conclusion = Column(Text, nullable=True)  # Заключення лікаря
    prognosis = Column(String(200), nullable=True)  # Прогноз
    
    # Follow up
    next_visit_date = Column(Date, nullable=True)  # Дата наступного відвідування
    next_visit_reason = Column(String(300), nullable=True)  # Причина наступного візиту
    
    # Sick leave / Medical certificate
    sick_leave_required = Column(Boolean, default=False)  # Потрібен лікарняний
    sick_leave_days = Column(Integer, nullable=True)  # Кількість днів лікарняного
    sick_leave_from = Column(Date, nullable=True)  # Лікарняний з
    sick_leave_to = Column(Date, nullable=True)  # Лікарняний по
    
    # Doctor signature info
    doctor_signature_name = Column(String(200), nullable=True)  # ПІБ лікаря для підпису
    doctor_position = Column(String(200), nullable=True)  # Посада
    doctor_specialty = Column(String(200), nullable=True)  # Спеціальність
    signature_date = Column(DateTime, nullable=True)  # Дата підписання
    is_signed = Column(Boolean, default=False)  # Чи підписаний звіт
    
    # Report file (HTML/PDF)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("UserORM", foreign_keys=[patient_id], back_populates="doctor_reports_received")
    doctor = relationship("UserORM", foreign_keys=[doctor_id], back_populates="doctor_reports_created")
    
    def __repr__(self) -> str:
        return f"<DoctorReportORM(id={self.id}, report_number={self.report_number}, patient_id={self.patient_id}, doctor_id={self.doctor_id})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "report_number": self.report_number,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "chief_complaint": self.chief_complaint,
            "preliminary_diagnosis": self.preliminary_diagnosis,
            "final_diagnosis": self.final_diagnosis,
            "diagnosis_code_icd": self.diagnosis_code_icd,
            "treatment_plan": self.treatment_plan,
            "next_visit_date": self.next_visit_date.isoformat() if self.next_visit_date else None,
            "doctor_signature_name": self.doctor_signature_name,
            "doctor_position": self.doctor_position,
            "is_signed": self.is_signed,
            "signature_date": self.signature_date.isoformat() if self.signature_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def sign(self, doctor_name: str, position: str, specialty: str = None):
        """Sign the report."""
        self.is_signed = True
        self.signature_date = datetime.utcnow()
        self.doctor_signature_name = doctor_name
        self.doctor_position = position
        if specialty:
            self.doctor_specialty = specialty
