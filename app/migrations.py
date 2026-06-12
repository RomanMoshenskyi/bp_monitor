from __future__ import annotations

from pathlib import Path

from .auth import ROLE_ADMIN, ROLE_DOCTOR, ROLE_PATIENT, _hash_password
from .database import connect

AUTH_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema_auth.sql"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def users_table_exists(conn) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'users'
            )
            """
        )
        return bool(cur.fetchone()[0])


def run_migrations(conn=None) -> None:
    own = conn is None
    if own:
        conn = connect()
    try:
        if not users_table_exists(conn):
            sql = AUTH_SCHEMA_PATH.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            _seed_default_users(conn)
            _migrate_legacy_measurements(conn)
            conn.commit()
        _migrate_email_column(conn)
        _migrate_soft_delete(conn)
        _migrate_doctor_patient_assignments(conn)
        if own:
            conn.commit()
    finally:
        if own and conn is not None:
            conn.close()


def _migrate_email_column(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'email'
            )
            """
        )
        if cur.fetchone()[0]:
            return
        cur.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE")


def _migrate_soft_delete(conn) -> None:
    """Apply 004_add_soft_delete.sql if deleted_at column is not yet present."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'measurements'
                  AND column_name = 'deleted_at'
            )
            """
        )
        if cur.fetchone()[0]:
            return
    sql_path = MIGRATIONS_DIR / "004_add_soft_delete.sql"
    if sql_path.exists():
        sql = sql_path.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def _migrate_doctor_patient_assignments(conn) -> None:
    """Apply 005_doctor_patient_assignment.sql if table doesn't exist yet."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'doctor_patient_assignments'
            )
            """
        )
        if cur.fetchone()[0]:
            return
    sql_path = MIGRATIONS_DIR / "005_doctor_patient_assignment.sql"
    if sql_path.exists():
        sql = sql_path.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def _seed_default_users(conn) -> None:
    defaults = [
        ("admin", "AdminPass123", "Адміністратор", ROLE_ADMIN),
        ("doctor", "DoctorPass123", "Лікар Іваненко", ROLE_DOCTOR),
        ("patient", "PatientPass123", "Пацієнт Демо", ROLE_PATIENT),
    ]
    with conn.cursor() as cur:
        for username, password, full_name, role in defaults:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                continue
            age = 30 if role == ROLE_PATIENT else None
            cur.execute(
                """
                INSERT INTO users (username, password_hash, full_name, role, age)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (username, _hash_password(password), full_name, role, age),
            )


def _migrate_legacy_measurements(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE role = %s ORDER BY id LIMIT 1", (ROLE_PATIENT,))
        row = cur.fetchone()
        if not row:
            return
        patient_id = row[0]
        cur.execute(
            "UPDATE measurements SET user_id = %s WHERE user_id IS NULL",
            (patient_id,),
        )
