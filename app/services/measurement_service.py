from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from ..analytics import summary
from ..models import Measurement
from .validation_service import ValidationService

if TYPE_CHECKING:
    from ..storage import PostgresStorage


class MeasurementService:
    """Encapsulates measurement business logic; delegates persistence to storage."""

    def __init__(self, storage: "PostgresStorage") -> None:
        self._storage = storage
        self._validator = ValidationService()

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def create_measurement(
        self,
        timestamp: str,
        systolic: int,
        diastolic: int,
        pulse: int,
        mood: str,
        notes: str,
        atmospheric_pressure: Optional[int],
        medication_taken: bool,
        activity_level: str,
        patient_id: Optional[int] = None,
    ) -> Measurement:
        errors = self._validator.validate_measurement(systolic, diastolic, pulse, timestamp)
        if errors:
            raise ValueError(self._validator.format_errors(errors))

        measurement = Measurement(
            id=uuid.uuid4().hex[:8],
            timestamp=timestamp,
            systolic=systolic,
            diastolic=diastolic,
            pulse=pulse,
            mood=mood,
            notes=notes,
            atmospheric_pressure=atmospheric_pressure,
            medication_taken=medication_taken,
            activity_level=activity_level,
        )
        self._storage.add_measurement(measurement, patient_id)
        return measurement

    def delete_measurement(
        self, measurement_id: str, patient_id: Optional[int] = None
    ) -> None:
        self._storage.delete_measurement(measurement_id, patient_id)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_measurements(self, patient_id: Optional[int] = None) -> List[Measurement]:
        return self._storage.get_measurements(patient_id)

    def get_summary(self, patient_id: Optional[int] = None) -> dict:
        return summary(self.get_measurements(patient_id))
