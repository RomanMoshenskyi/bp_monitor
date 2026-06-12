from __future__ import annotations

from typing import List

from ..database import db_cursor
from ..models import Measurement, _parse_timestamp, _row_to_measurement


class MeasurementRepository:
    """Data-access object for the measurements table."""

    def get_all(self, user_id: int) -> List[Measurement]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, timestamp, systolic, diastolic, pulse, mood, notes,
                       atmospheric_pressure, medication_taken, activity_level
                FROM measurements
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY timestamp
                """,
                (user_id,),
            )
            return [_row_to_measurement(row) for row in cur.fetchall()]

    def get_paginated(
        self, user_id: int, limit: int, offset: int
    ) -> List[Measurement]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, timestamp, systolic, diastolic, pulse, mood, notes,
                       atmospheric_pressure, medication_taken, activity_level
                FROM measurements
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
            return [_row_to_measurement(row) for row in cur.fetchall()]

    def count(self, user_id: int) -> int:
        with db_cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM measurements WHERE user_id = %s AND deleted_at IS NULL",
                (user_id,),
            )
            return cur.fetchone()[0]

    def add(self, measurement: Measurement, user_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO measurements (
                    id, user_id, timestamp, systolic, diastolic, pulse, mood, notes,
                    atmospheric_pressure, medication_taken, activity_level
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    timestamp = EXCLUDED.timestamp,
                    systolic = EXCLUDED.systolic,
                    diastolic = EXCLUDED.diastolic,
                    pulse = EXCLUDED.pulse,
                    mood = EXCLUDED.mood,
                    notes = EXCLUDED.notes,
                    atmospheric_pressure = EXCLUDED.atmospheric_pressure,
                    medication_taken = EXCLUDED.medication_taken,
                    activity_level = EXCLUDED.activity_level
                """,
                (
                    measurement.id,
                    user_id,
                    _parse_timestamp(measurement.timestamp),
                    measurement.systolic,
                    measurement.diastolic,
                    measurement.pulse,
                    measurement.mood,
                    measurement.notes,
                    measurement.atmospheric_pressure,
                    measurement.medication_taken,
                    measurement.activity_level,
                ),
            )

    def soft_delete(self, measurement_id: str, user_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE measurements SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s",
                (measurement_id, user_id),
            )

    def hard_delete(self, measurement_id: str, user_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "DELETE FROM measurements WHERE id = %s AND user_id = %s",
                (measurement_id, user_id),
            )
