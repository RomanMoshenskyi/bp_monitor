from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List


DATE_FMT = "%Y-%m-%d %H:%M"


@dataclass
class ValidationError:
    field: str
    message: str


class ValidationService:
    """Server-side validation: all rules enforced independently of the UI."""

    def validate_measurement(
        self,
        systolic: int,
        diastolic: int,
        pulse: int,
        timestamp: str,
    ) -> List[ValidationError]:
        errors: List[ValidationError] = []

        # Timestamp
        try:
            datetime.strptime(timestamp, DATE_FMT)
        except ValueError:
            errors.append(ValidationError(
                "timestamp",
                f"Некоректний формат дати та часу. Очікується: {DATE_FMT}",
            ))

        # Systolic range
        if not (60 <= systolic <= 240):
            errors.append(ValidationError(
                "systolic",
                "Систолічний тиск має бути в діапазоні 60–240 мм рт. ст.",
            ))

        # Diastolic range
        if not (40 <= diastolic <= 150):
            errors.append(ValidationError(
                "diastolic",
                "Діастолічний тиск має бути в діапазоні 40–150 мм рт. ст.",
            ))

        # Systolic > diastolic (only when both are in valid range)
        if 60 <= systolic <= 240 and 40 <= diastolic <= 150:
            if systolic <= diastolic:
                errors.append(ValidationError(
                    "systolic",
                    "Систолічний тиск має бути більшим за діастолічний.",
                ))

        # Pulse range
        if not (35 <= pulse <= 220):
            errors.append(ValidationError(
                "pulse",
                "Пульс має бути в діапазоні 35–220 уд/хв.",
            ))

        return errors

    def validate_user_profile(
        self,
        name: str,
        age: int,
        target_systolic: int,
        target_diastolic: int,
        target_pulse: int,
    ) -> List[ValidationError]:
        errors: List[ValidationError] = []

        if not name or len(name.strip()) < 2:
            errors.append(ValidationError("name", "Ім'я має містити щонайменше 2 символи."))

        if not (1 <= age <= 120):
            errors.append(ValidationError("age", "Вік має бути в діапазоні 1–120 років."))

        if not (80 <= target_systolic <= 180):
            errors.append(ValidationError(
                "target_systolic",
                "Цільовий систолічний тиск має бути в діапазоні 80–180.",
            ))

        if not (50 <= target_diastolic <= 120):
            errors.append(ValidationError(
                "target_diastolic",
                "Цільовий діастолічний тиск має бути в діапазоні 50–120.",
            ))

        if not (40 <= target_pulse <= 150):
            errors.append(ValidationError(
                "target_pulse",
                "Цільовий пульс має бути в діапазоні 40–150.",
            ))

        if (80 <= target_systolic <= 180) and (50 <= target_diastolic <= 120):
            if target_systolic <= target_diastolic:
                errors.append(ValidationError(
                    "target_systolic",
                    "Цільовий систолічний тиск має бути більшим за цільовий діастолічний.",
                ))

        return errors

    def format_errors(self, errors: List[ValidationError]) -> str:
        """Return a human-readable summary of all errors."""
        return "\n".join(f"• {e.message}" for e in errors)
