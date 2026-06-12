from __future__ import annotations

from typing import List

from ..database import db_cursor


class AssignmentRepository:
    """Manages doctor-patient assignments."""

    def assign(self, doctor_id: int, patient_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO doctor_patient_assignments (doctor_id, patient_id)
                VALUES (%s, %s)
                ON CONFLICT (doctor_id, patient_id) DO NOTHING
                """,
                (doctor_id, patient_id),
            )

    def unassign(self, doctor_id: int, patient_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "DELETE FROM doctor_patient_assignments WHERE doctor_id = %s AND patient_id = %s",
                (doctor_id, patient_id),
            )

    def get_patients_for_doctor(self, doctor_id: int) -> List[int]:
        with db_cursor() as cur:
            cur.execute(
                "SELECT patient_id FROM doctor_patient_assignments WHERE doctor_id = %s ORDER BY assigned_at",
                (doctor_id,),
            )
            return [row[0] for row in cur.fetchall()]

    def get_doctors_for_patient(self, patient_id: int) -> List[int]:
        with db_cursor() as cur:
            cur.execute(
                "SELECT doctor_id FROM doctor_patient_assignments WHERE patient_id = %s ORDER BY assigned_at",
                (patient_id,),
            )
            return [row[0] for row in cur.fetchall()]

    def is_assigned(self, doctor_id: int, patient_id: int) -> bool:
        with db_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM doctor_patient_assignments WHERE doctor_id = %s AND patient_id = %s",
                (doctor_id, patient_id),
            )
            return cur.fetchone() is not None
