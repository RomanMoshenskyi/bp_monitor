from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..storage import PostgresStorage


class ExportService:
    """Handles all export/backup functionality."""

    def __init__(self, storage: "PostgresStorage") -> None:
        self._storage = storage

    def export_to_json(
        self, target_path: str | Path, patient_id: Optional[int] = None
    ) -> None:
        self._storage.export_to_json(target_path, patient_id)

    def export_to_csv(
        self, target_path: str | Path, patient_id: Optional[int] = None
    ) -> None:
        measurements = self._storage.get_measurements(patient_id)
        target = Path(target_path)

        with target.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Дата/Час", "Систолічний", "Діастолічний", "Пульс",
                "Стан", "Примітки", "Атм. тиск", "Ліки", "Активність",
            ])
            for m in measurements:
                writer.writerow([
                    m.id,
                    m.timestamp,
                    m.systolic,
                    m.diastolic,
                    m.pulse,
                    m.mood,
                    m.notes,
                    m.atmospheric_pressure if m.atmospheric_pressure is not None else "",
                    "Так" if m.medication_taken else "Ні",
                    m.activity_level,
                ])
