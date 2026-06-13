from __future__ import annotations

from typing import List, Tuple

from ..database import db_cursor


class RecommendationRepository:
    """Data-access object for doctor_recommendations table."""

    def get_for_patient(self, patient_id: int, limit: int = 20) -> List[str]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT recommendation FROM doctor_recommendations
                WHERE patient_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (patient_id, limit),
            )
            return [row[0] for row in cur.fetchall()]

    def get_for_patient_with_doctor(
        self, patient_id: int, limit: int = 20
    ) -> List[Tuple[str, str, str]]:
        """Returns list of (recommendation_text, doctor_full_name, doctor_email_or_empty)."""
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT dr.recommendation,
                       u.full_name,
                       COALESCE(u.email, '') AS email
                FROM doctor_recommendations dr
                JOIN users u ON u.id = dr.doctor_id
                WHERE dr.patient_id = %s
                ORDER BY dr.created_at DESC
                LIMIT %s
                """,
                (patient_id, limit),
            )
            return [(row[0], row[1], row[2]) for row in cur.fetchall()]

    def add(self, patient_id: int, doctor_id: int, text: str) -> None:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO doctor_recommendations (patient_id, doctor_id, recommendation)
                VALUES (%s, %s, %s)
                """,
                (patient_id, doctor_id, text.strip()),
            )

    def delete_by_id(self, recommendation_id: int, doctor_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "DELETE FROM doctor_recommendations WHERE id = %s AND doctor_id = %s",
                (recommendation_id, doctor_id),
            )
