"""Measurement DTOs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MeasurementDTO:
    """Measurement data transfer object."""
    id: int
    user_id: int
    systolic: int
    diastolic: int
    pulse: Optional[int]
    measured_at: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    notes: Optional[str]
    weather_snapshot_id: Optional[int]
    # Additional fields from original app
    city: Optional[str] = None
    mood: Optional[str] = None
    activity_level: Optional[str] = None
    took_medication: bool = False
    medication_ids: Optional[list] = None
    # Weather data
    pressure_mmhg: Optional[int] = None
    temperature: Optional[float] = None
    humidity: Optional[int] = None
    weather_description: Optional[str] = None

    @property
    def pressure_status(self) -> str:
        """Quick status check."""
        if self.systolic > 140 or self.diastolic > 90:
            return "high"
        elif self.systolic < 90 or self.diastolic < 60:
            return "low"
        return "normal"


@dataclass
class MeasurementCreateDTO:
    """DTO for creating new measurement."""
    user_id: int
    systolic: int
    diastolic: int
    pulse: Optional[int] = None
    measured_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    # Additional fields from original app
    city: Optional[str] = None  # City for weather lookup
    mood: Optional[str] = None  # Mood/state: calm, work_day, stress
    activity_level: Optional[str] = None  # Activity: low, medium, high
    took_medication: bool = False  # Whether patient took medication
    medication_ids: Optional[list] = None  # List of medication IDs taken


@dataclass
class DateRangeDTO:
    """Date range for queries."""
    start_date: datetime
    end_date: datetime
