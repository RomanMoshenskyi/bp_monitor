from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from typing import List, Optional

from .database import db_cursor
from .logging_config import get_logger

_log = get_logger(__name__)

ROLE_PATIENT = "patient"
ROLE_DOCTOR = "doctor"
ROLE_ADMIN = "admin"

ROLE_LABELS = {
    ROLE_PATIENT: "Пацієнт",
    ROLE_DOCTOR: "Лікар",
    ROLE_ADMIN: "Адміністратор",
}

_USER_SELECT = """
    id, username, password_hash, full_name, role, age,
    target_systolic, target_diastolic, target_pulse, is_active, email
"""


@dataclass
class User:
    id: int
    username: str
    full_name: str
    role: str
    age: Optional[int] = None
    target_systolic: int = 120
    target_diastolic: int = 80
    target_pulse: int = 75
    is_active: bool = True
    email: Optional[str] = None

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)


def _validate_password_strength(password: str) -> None:
    """Перевірити надійність пароля. Викидає ValueError при невідповідності."""
    if len(password) < 8:
        raise ValueError("Пароль має містити щонайменше 8 символів")
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_upper and has_lower and has_digit):
        raise ValueError(
            "Пароль має містити хоча б одну велику літеру, "
            "одну малу літеру та одну цифру"
        )


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest_hex = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return secrets.compare_digest(digest.hex(), digest_hex)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_email(email: str) -> None:
    email = _normalize_email(email)
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("Введіть коректну електронну пошту")


def _row_to_user(row: tuple) -> User:
    uid, username, _hash, full_name, role, age, ts, td, tp, is_active, email = row
    return User(
        id=uid,
        username=username,
        full_name=full_name,
        role=role,
        age=age,
        target_systolic=ts or 120,
        target_diastolic=td or 80,
        target_pulse=tp or 75,
        is_active=is_active,
        email=email,
    )


class AuthService:
    def __init__(self):
        self._audit_service = None
    
    def _get_audit_service(self):
        """Lazy load audit service."""
        if self._audit_service is None:
            try:
                from .infrastructure.orm.base import SessionLocal
                from .application.services.audit_service import AuditService
                db = SessionLocal()
                self._audit_service = AuditService(db)
            except:
                self._audit_service = None
        return self._audit_service
    
    def login(self, username: str, password: str) -> Optional[User]:
        with db_cursor() as cur:
            cur.execute(
                f"""
                SELECT {_USER_SELECT}
                FROM users
                WHERE username = %s AND is_active = TRUE AND deleted_at IS NULL
                """,
                (username.strip().lower(),),
            )
            row = cur.fetchone()
        if not row or not _verify_password(password, row[2]):
            _log.warning("login_failed", username=username)
            return None
        user = _row_to_user(row)
        _log.info("user_login", user_id=user.id, role=user.role)
        
        # Log to audit service
        audit = self._get_audit_service()
        if audit:
            try:
                audit.log(user.id, "login", f"User {username} logged in")
            except:
                pass
        
        return user

    def register(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str,
        age: int,
    ) -> User:
        """Публічна реєстрація — лише пацієнти."""
        user = self._insert_user(
            username=username,
            password=password,
            full_name=full_name,
            role=ROLE_PATIENT,
            age=age,
            email=email,
        )
        
        # Log to audit service
        audit = self._get_audit_service()
        if audit:
            try:
                audit.log(user.id, "user_created", f"User {username} registered")
            except:
                pass
        
        return user

    def _insert_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str,
        age: Optional[int] = None,
        email: Optional[str] = None,
    ) -> User:
        _validate_password_strength(password)
        _log.info("user_register", username=username.strip().lower(), role=role)
        uname = username.strip().lower()
        email_norm = _normalize_email(email) if email else None
        if email_norm:
            _validate_email(email_norm)

        with db_cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (uname,))
            if cur.fetchone():
                raise ValueError("Такий логін уже зайнятий")
            if email_norm:
                cur.execute("SELECT 1 FROM users WHERE email = %s", (email_norm,))
                if cur.fetchone():
                    raise ValueError("Така електронна пошта вже зареєстрована")
            cur.execute(
                f"""
                INSERT INTO users (
                    username, password_hash, full_name, role, age, email,
                    target_systolic, target_diastolic, target_pulse
                ) VALUES (%s, %s, %s, %s, %s, %s, 120, 80, 75)
                RETURNING {_USER_SELECT}
                """,
                (uname, _hash_password(password), full_name.strip(), role, age, email_norm),
            )
            row = cur.fetchone()
        return _row_to_user(row)

    def list_users(self, role: Optional[str] = None) -> List[User]:
        query = f"SELECT {_USER_SELECT} FROM users WHERE deleted_at IS NULL"
        params: tuple = ()
        if role:
            query += " AND role = %s"
            params = (role,)
        query += " ORDER BY role, full_name"
        with db_cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        return [_row_to_user(r) for r in rows]

    def list_patients(self) -> List[User]:
        return self.list_users(ROLE_PATIENT)

    def get_user(self, user_id: int) -> Optional[User]:
        with db_cursor() as cur:
            cur.execute(
                f"SELECT {_USER_SELECT} FROM users WHERE id = %s AND deleted_at IS NULL",
                (user_id,),
            )
            row = cur.fetchone()
        return _row_to_user(row) if row else None

    def set_user_active(self, user_id: int, active: bool) -> None:
        with db_cursor() as cur:
            cur.execute("UPDATE users SET is_active = %s WHERE id = %s", (active, user_id))

    def update_user_thresholds(
        self,
        user_id: int,
        target_systolic: int,
        target_diastolic: int,
        target_pulse: int,
        age: Optional[int] = None,
    ) -> None:
        with db_cursor() as cur:
            if age is not None:
                cur.execute(
                    """
                    UPDATE users
                    SET target_systolic = %s, target_diastolic = %s, target_pulse = %s, age = %s
                    WHERE id = %s
                    """,
                    (target_systolic, target_diastolic, target_pulse, age, user_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE users
                    SET target_systolic = %s, target_diastolic = %s, target_pulse = %s
                    WHERE id = %s
                    """,
                    (target_systolic, target_diastolic, target_pulse, user_id),
                )

    def reset_password(self, user_id: int, new_password: str) -> None:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (_hash_password(new_password), user_id),
            )

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str,
        age: Optional[int] = None,
        email: Optional[str] = None,
    ) -> User:
        if role not in (ROLE_PATIENT, ROLE_DOCTOR, ROLE_ADMIN):
            raise ValueError("Невідома роль")
        return self._insert_user(username, password, full_name, role, age, email)

    def update_user(
        self,
        user_id: int,
        full_name: str,
        role: str,
        age: Optional[int] = None,
        email: Optional[str] = None,
    ) -> None:
        if role not in (ROLE_PATIENT, ROLE_DOCTOR, ROLE_ADMIN):
            raise ValueError("Невідома роль")
        email_norm = _normalize_email(email) if email else None
        if email_norm:
            _validate_email(email_norm)
        with db_cursor() as cur:
            if email_norm:
                cur.execute(
                    "SELECT 1 FROM users WHERE email = %s AND id <> %s",
                    (email_norm, user_id),
                )
                if cur.fetchone():
                    raise ValueError("Така електронна пошта вже зареєстрована")
            cur.execute(
                """
                UPDATE users
                SET full_name = %s, role = %s, age = %s, email = %s
                WHERE id = %s
                """,
                (full_name.strip(), role, age, email_norm, user_id),
            )
