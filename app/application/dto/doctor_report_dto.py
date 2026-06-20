"""Doctor Report DTOs - Data transfer objects for medical reports."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class DoctorReportCreateDTO:
    """DTO for creating a new doctor report."""
    
    # Required
    patient_id: int
    doctor_id: int
    
    # Report info
    report_date: Optional[date] = None
    
    # Patient complaints and history
    chief_complaint: Optional[str] = None  # Головні скарги
    history_illness: Optional[str] = None  # Анамнез захворювання
    history_life: Optional[str] = None  # Анамнез життя
    
    # Objective examination
    objective_exam: Optional[str] = None  # Об'єктивний стан
    general_condition: Optional[str] = None  # Загальний стан
    consciousness: Optional[str] = None  # Свідомість
    body_temperature: Optional[str] = None  # Температура тіла
    skin_condition: Optional[str] = None  # Стан шкіри
    
    # Vital signs at examination
    heart_rate: Optional[int] = None  # ЧСС
    respiratory_rate: Optional[int] = None  # ЧДД
    blood_pressure_sys: Optional[int] = None  # АТ систолічне
    blood_pressure_dia: Optional[int] = None  # АТ діастолічне
    
    # Cardiovascular system
    heart_sounds: Optional[str] = None  # Тони серця
    pulse_rhythm: Optional[str] = None  # Ритм пульсу
    pulse_character: Optional[str] = None  # Характер пульсу
    
    # Diagnosis
    preliminary_diagnosis: Optional[str] = None  # Попередній діагноз
    final_diagnosis: Optional[str] = None  # Заключний діагноз
    diagnosis_code_icd: Optional[str] = None  # Код МКХ-10
    
    # Examination results
    ecg_results: Optional[str] = None  # Результати ЕКГ
    xray_results: Optional[str] = None  # Результати рентгену
    lab_results: Optional[str] = None  # Лабораторні дані
    other_exams: Optional[str] = None  # Інші обстеження
    
    # Treatment and recommendations
    treatment_plan: Optional[str] = None  # План лікування
    prescriptions: Optional[str] = None  # Призначення (ліки)
    procedures: Optional[str] = None  # Процедури
    lifestyle_recommendations: Optional[str] = None  # Рекомендації щодо способу життя
    diet_recommendations: Optional[str] = None  # Дієтичні рекомендації
    activity_recommendations: Optional[str] = None  # Рекомендації щодо активності
    
    # Doctor's conclusions
    doctor_conclusion: Optional[str] = None  # Заключення лікаря
    prognosis: Optional[str] = None  # Прогноз
    
    # Follow up
    next_visit_date: Optional[date] = None  # Дата наступного відвідування
    next_visit_reason: Optional[str] = None  # Причина наступного візиту
    
    # Sick leave / Medical certificate
    sick_leave_required: bool = False  # Потрібен лікарняний
    sick_leave_days: Optional[int] = None  # Кількість днів лікарняного
    sick_leave_from: Optional[date] = None  # Лікарняний з
    sick_leave_to: Optional[date] = None  # Лікарняний по


@dataclass
class DoctorReportDTO:
    """DTO for doctor report response."""
    
    id: int
    report_number: str
    patient_id: int
    doctor_id: int
    report_date: Optional[date]
    
    # Summary fields
    chief_complaint: Optional[str]
    preliminary_diagnosis: Optional[str]
    final_diagnosis: Optional[str]
    diagnosis_code_icd: Optional[str]
    treatment_plan: Optional[str]
    prescriptions: Optional[str]
    doctor_conclusion: Optional[str]
    next_visit_date: Optional[date]
    
    # Signature info
    is_signed: bool
    doctor_signature_name: Optional[str]
    doctor_position: Optional[str]
    doctor_specialty: Optional[str]
    signature_date: Optional[datetime]
    
    # File info
    file_path: Optional[str]
    
    # Timestamps
    created_at: Optional[datetime]
    
    def to_summary_dict(self) -> dict:
        """Get summary for list views."""
        return {
            "id": self.id,
            "report_number": self.report_number,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "preliminary_diagnosis": self.preliminary_diagnosis,
            "final_diagnosis": self.final_diagnosis,
            "is_signed": self.is_signed,
            "doctor_signature_name": self.doctor_signature_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
