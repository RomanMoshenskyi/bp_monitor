"""Prescription DTOs - Data transfer objects for prescriptions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional, List


@dataclass
class PrescriptionCreateDTO:
    """DTO for creating a new prescription."""
    
    # Required
    doctor_id: int
    patient_id: int
    medication_name: str
    dosage: str
    frequency_per_day: int
    
    # Optional medication details
    medication_form: Optional[str] = None  # Таблетки, капсули, сироп...
    specific_times: Optional[List[time]] = None  # Конкретні часи прийому
    
    # Duration
    duration_days: Optional[int] = None  # Тривалість курсу
    start_date: Optional[date] = None
    prescription_date: Optional[date] = None
    
    # Administration instructions
    take_with_food: Optional[bool] = None
    take_before_food: Optional[bool] = None
    take_after_food: Optional[bool] = None
    special_instructions: Optional[str] = None
    
    # Doctor notes
    prescribed_for: Optional[str] = None  # Показання
    contraindications: Optional[str] = None  # Протипоказання
    side_effects_notes: Optional[str] = None  # Побічні ефекти
    interactions_warning: Optional[str] = None  # Взаємодія з іншими ліками


@dataclass
class PrescriptionDTO:
    """DTO for prescription response."""
    
    id: int
    prescription_number: str
    doctor_id: int
    patient_id: int
    prescription_date: Optional[date]
    
    # Medication details
    medication_name: str
    medication_form: Optional[str]
    dosage: str
    frequency_per_day: int
    specific_times: Optional[List[str]]  # ISO format times
    
    # Duration
    duration_days: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    
    # Administration
    take_with_food: Optional[bool]
    special_instructions: Optional[str]
    prescribed_for: Optional[str]
    
    # Status
    status: str
    patient_notified: bool
    notification_seen_at: Optional[datetime]
    notification_accepted: Optional[bool]
    
    # Timestamps
    created_at: Optional[datetime]
    
    def to_summary_dict(self) -> dict:
        """Get summary for list views."""
        return {
            "id": self.id,
            "prescription_number": self.prescription_number,
            "medication_name": self.medication_name,
            "dosage": self.dosage,
            "frequency_per_day": self.frequency_per_day,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "patient_notified": self.patient_notified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class PrescriptionIntakeDTO:
    """DTO for scheduled medication intake."""
    
    id: int
    prescription_id: Optional[int]
    medication_id: Optional[int]
    scheduled_time: Optional[datetime]
    taken_at: Optional[datetime]
    status: str  # pending, taken, missed, skipped, late, early
    taken_on_time: Optional[bool]
    minutes_delay: Optional[int]
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    
    def is_overdue(self) -> bool:
        """Check if this intake is overdue (more than 5 hours grace period)."""
        if self.status != "pending" or not self.scheduled_time:
            return False
        # Use local time and check if more than 5 hours passed (300 minutes)
        minutes_late = self.minutes_late()
        return minutes_late is not None and minutes_late > 300
    
    def is_in_grace_period(self) -> bool:
        """Check if intake is in grace period (0-5 hours after scheduled time)."""
        if self.status != "pending" or not self.scheduled_time:
            return False
        minutes_late = self.minutes_late()
        return minutes_late is not None and 0 < minutes_late <= 300
    
    def minutes_late(self) -> Optional[int]:
        """Get minutes since scheduled time (positive if late)."""
        if not self.scheduled_time:
            return None
        delta = datetime.now() - self.scheduled_time
        return int(delta.total_seconds() / 60)
    
    def time_until(self) -> Optional[int]:
        """Get minutes until scheduled time (negative if overdue)."""
        if not self.scheduled_time:
            return None
        delta = self.scheduled_time - datetime.now()
        return int(delta.total_seconds() / 60)


@dataclass
class IntakeRecordDTO:
    """DTO for recording an intake."""
    
    intake_id: int
    taken_at: datetime
    dosage: Optional[float] = None
    dosage_unit: Optional[str] = None
    taken_with_food: Optional[bool] = None
    notes: Optional[str] = None


@dataclass
class AdherenceStatsDTO:
    """DTO for adherence statistics."""
    
    total: int
    taken: int
    late: int
    missed: int
    skipped: int
    adherence_rate: float
    days_analyzed: int
    
    def get_grade(self) -> str:
        """Get letter grade based on adherence."""
        if self.adherence_rate >= 95:
            return "A"
        elif self.adherence_rate >= 85:
            return "B"
        elif self.adherence_rate >= 70:
            return "C"
        elif self.adherence_rate >= 50:
            return "D"
        else:
            return "F"
    
    def get_status_text(self) -> str:
        """Get human-readable status."""
        if self.adherence_rate >= 90:
            return "Відмінна прихильність"
        elif self.adherence_rate >= 75:
            return "Добра прихильність"
        elif self.adherence_rate >= 60:
            return "Задовільна прихильність"
        elif self.adherence_rate >= 40:
            return "Низька прихильність"
        else:
            return "Критична прихильність - потрібна увага лікаря"


@dataclass
class CalendarDayDTO:
    """DTO for calendar day adherence data."""
    
    date: str  # ISO format date
    day: int
    level: int  # 0-4 (0=no meds, 1=poor, 2=fair, 3=good, 4=perfect)
    total: int
    taken: int
    missed: int
    
    def get_color(self) -> str:
        """Get color for this day's adherence level."""
        colors = {
            0: "#ebedf0",  # Gray - no meds
            1: "#9be9a8",  # Light green - poor
            2: "#40c463",  # Green - fair
            3: "#30a14e",  # Darker green - good
            4: "#216e39",  # Darkest green - perfect
        }
        return colors.get(self.level, "#ebedf0")


@dataclass
class CalendarMonthDTO:
    """DTO for calendar month data."""
    
    year: int
    month: int
    days: List[CalendarDayDTO]
    
    def get_adherence_percentage(self) -> float:
        """Get overall adherence for the month."""
        total_scheduled = sum(d.total for d in self.days if d.total > 0)
        total_taken = sum(d.taken for d in self.days)
        
        if total_scheduled == 0:
            return 0.0
        return round(total_taken / total_scheduled * 100, 1)
