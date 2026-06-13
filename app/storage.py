from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .auth import User
from .database import connect, init_schema
from .models import Measurement, SystemThresholds, _parse_timestamp
from .repositories.measurement_repository import MeasurementRepository
from .repositories.recommendation_repository import RecommendationRepository
from .repositories.user_repository import UserRepository
from .services.validation_service import ValidationService


class PostgresStorage:
    def __init__(self, user: User) -> None:
        init_schema()
        self.user = user
        self._validator = ValidationService()
        self._measurements = MeasurementRepository()
        self._users = UserRepository()
        self._recommendations = RecommendationRepository()

    def get_profile(self) -> Dict[str, Any]:
        u = self.user
        return {
            "name": u.full_name,
            "age": u.age or 28,
            "target_systolic": u.target_systolic,
            "target_diastolic": u.target_diastolic,
            "target_pulse": u.target_pulse,
        }

    def load(self, patient_id: Optional[int] = None) -> Dict[str, Any]:
        pid = patient_id or self.user.id
        patient = self._users.get_by_id(pid)
        profile = {
            "name": patient.full_name if patient else "",
            "age": patient.age if patient else 28,
            "target_systolic": patient.target_systolic if patient else 120,
            "target_diastolic": patient.target_diastolic if patient else 80,
            "target_pulse": patient.target_pulse if patient else 75,
        }
        return {
            "profile": profile,
            "measurements": [asdict(m) for m in self.get_measurements(pid)],
        }

    def get_measurements(self, patient_id: Optional[int] = None) -> List[Measurement]:
        pid = patient_id or self.user.id
        return self._measurements.get_all(pid)

    def get_measurements_paginated(
        self, patient_id: Optional[int] = None, limit: int = 50, offset: int = 0
    ) -> List[Measurement]:
        pid = patient_id or self.user.id
        return self._measurements.get_paginated(pid, limit, offset)

    def count_measurements(self, patient_id: Optional[int] = None) -> int:
        pid = patient_id or self.user.id
        return self._measurements.count(pid)

    def add_measurement(self, measurement: Measurement, patient_id: Optional[int] = None) -> None:
        errors = self._validator.validate_measurement(
            measurement.systolic,
            measurement.diastolic,
            measurement.pulse,
            measurement.timestamp,
        )
        if errors:
            raise ValueError(self._validator.format_errors(errors))
        pid = patient_id or self.user.id
        self._measurements.add(measurement, pid)

    def delete_measurement(self, measurement_id: str, patient_id: Optional[int] = None) -> None:
        """Soft-delete: marks record with deleted_at timestamp instead of hard removal."""
        pid = patient_id or self.user.id
        self._measurements.soft_delete(measurement_id, pid)

    def update_profile(self, profile: Dict[str, Any]) -> None:
        self._users.update_profile(
            user_id=self.user.id,
            full_name=profile.get("name", self.user.full_name),
            age=profile.get("age", self.user.age or 28),
            target_systolic=profile.get("target_systolic", 120),
            target_diastolic=profile.get("target_diastolic", 80),
            target_pulse=profile.get("target_pulse", 75),
        )
        self.user.full_name = profile.get("name", self.user.full_name)
        self.user.age = profile.get("age", self.user.age)
        self.user.target_systolic = profile.get("target_systolic", self.user.target_systolic)
        self.user.target_diastolic = profile.get("target_diastolic", self.user.target_diastolic)
        self.user.target_pulse = profile.get("target_pulse", self.user.target_pulse)

    def export_to_json(self, target_path: str | Path, patient_id: Optional[int] = None) -> None:
        target = Path(target_path)
        data = self.load(patient_id)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def import_from_json(self, source_path: str | Path) -> dict:
        """Import measurements and profile from an exported JSON file.
        Returns a summary dict with keys 'imported', 'skipped', 'errors'."""
        source = Path(source_path)
        raw = source.read_text(encoding="utf-8")
        data = json.loads(raw)

        imported = 0
        skipped = 0
        errors = 0

        # Update profile if present
        profile = data.get("profile")
        if isinstance(profile, dict):
            try:
                self.update_profile(profile)
            except Exception:
                pass

        # Import measurements
        error_details: List[str] = []
        for item in data.get("measurements", []):
            try:
                ts   = item["timestamp"]
                sys_ = int(item["systolic"])
                dia_ = int(item["diastolic"])
                pls_ = int(item["pulse"])
                if self._measurements.exists_by_fingerprint(
                    self.user.id, ts, sys_, dia_, pls_
                ):
                    skipped += 1
                    continue
                m = Measurement(
                    id=str(uuid.uuid4()),
                    timestamp=ts,
                    systolic=sys_,
                    diastolic=dia_,
                    pulse=pls_,
                    mood=item.get("mood", "Спокійний"),
                    notes=item.get("notes", ""),
                    atmospheric_pressure=item.get("atmospheric_pressure"),
                    medication_taken=bool(item.get("medication_taken", False)),
                    activity_level=item.get("activity_level", "Низька"),
                )
                self._measurements.add(m, self.user.id)
                imported += 1
            except Exception as exc:
                errors += 1
                error_details.append(str(exc))

        return {"imported": imported, "skipped": skipped, "errors": errors, "error_details": error_details}

    def get_system_thresholds(self) -> SystemThresholds:
        from .database import db_cursor
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT systolic_high, diastolic_high, systolic_low, diastolic_low, pulse_high, pulse_low
                FROM system_thresholds ORDER BY id LIMIT 1
                """
            )
            row = cur.fetchone()
        if not row:
            return SystemThresholds()
        return SystemThresholds(*row)

    def update_system_thresholds(self, thresholds: SystemThresholds) -> None:
        from .database import db_cursor
        with db_cursor() as cur:
            cur.execute(
                """
                UPDATE system_thresholds
                SET systolic_high = %s, diastolic_high = %s, systolic_low = %s,
                    diastolic_low = %s, pulse_high = %s, pulse_low = %s,
                    updated_at = CURRENT_TIMESTAMP, updated_by = %s
                WHERE id = (SELECT id FROM system_thresholds ORDER BY id LIMIT 1)
                """,
                (
                    thresholds.systolic_high,
                    thresholds.diastolic_high,
                    thresholds.systolic_low,
                    thresholds.diastolic_low,
                    thresholds.pulse_high,
                    thresholds.pulse_low,
                    self.user.id,
                ),
            )

    def add_doctor_recommendation(self, patient_id: int, text: str) -> None:
        self._recommendations.add(patient_id, self.user.id, text)

    def get_doctor_recommendations(self, patient_id: int, limit: int = 20) -> List[str]:
        return self._recommendations.get_for_patient(patient_id, limit)

    def get_doctor_recommendations_with_doctor(
        self, patient_id: int, limit: int = 20
    ) -> List[tuple]:
        """Returns list of (text, doctor_name, doctor_email_or_empty)."""
        return self._recommendations.get_for_patient_with_doctor(patient_id, limit)


def create_storage(user: User) -> PostgresStorage:
    return PostgresStorage(user)


def check_database_connection() -> None:
    conn = connect()
    conn.close()
