"""Core domain models and helpers used across the application."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Measurement:
    id: str
    timestamp: str
    systolic: int
    diastolic: int
    pulse: int
    mood: str = "Спокійний"
    notes: str = ""
    atmospheric_pressure: Optional[int] = None
    medication_taken: bool = False
    activity_level: str = "Низька"


@dataclass
class SystemThresholds:
    systolic_high: int = 140
    diastolic_high: int = 90
    systolic_low: int = 90
    diastolic_low: int = 60
    pulse_high: int = 100
    pulse_low: int = 50


def _format_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def _parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def _row_to_measurement(row: tuple) -> Measurement:
    (
        mid,
        measured_at,
        systolic,
        diastolic,
        pulse,
        mood,
        notes,
        atmospheric_pressure,
        medication_taken,
        activity_level,
    ) = row
    return Measurement(
        id=mid,
        timestamp=_format_timestamp(measured_at),
        systolic=systolic,
        diastolic=diastolic,
        pulse=pulse,
        mood=mood or "Спокійний",
        notes=notes or "",
        atmospheric_pressure=atmospheric_pressure,
        medication_taken=bool(medication_taken),
        activity_level=activity_level or "Низька",
    )


def measurement_to_row(m: Measurement) -> list[str]:
    return [
        m.timestamp,
        f"{m.systolic}/{m.diastolic}",
        str(m.pulse),
        str(m.atmospheric_pressure) if m.atmospheric_pressure else "—",
        m.mood,
        "Так" if m.medication_taken else "Ні",
        m.activity_level,
        m.notes,
    ]
