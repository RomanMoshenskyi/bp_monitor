from __future__ import annotations

from typing import List, Optional

from ..auth import User, _hash_password
from ..database import db_cursor


def _row_to_user(row) -> User:
    return User(
        id=row[0],
        username=row[1],
        full_name=row[2],
        role=row[3],
        age=row[4],
        target_systolic=row[5],
        target_diastolic=row[6],
        target_pulse=row[7],
        is_active=bool(row[8]),
        email=row[9] if len(row) > 9 else None,
    )


_SELECT = """
    SELECT id, username, full_name, role, age,
           target_systolic, target_diastolic, target_pulse, is_active,
           COALESCE(email, NULL)
    FROM users
"""


class UserRepository:
    """Data-access object for the users table."""

    def get_by_id(self, user_id: int) -> Optional[User]:
        with db_cursor() as cur:
            cur.execute(_SELECT + "WHERE id = %s AND deleted_at IS NULL", (user_id,))
            row = cur.fetchone()
        return _row_to_user(row) if row else None

    def get_by_username(self, username: str) -> Optional[User]:
        with db_cursor() as cur:
            cur.execute(
                _SELECT + "WHERE username = %s AND deleted_at IS NULL",
                (username.strip().lower(),),
            )
            row = cur.fetchone()
        return _row_to_user(row) if row else None

    def get_by_role(self, role: str) -> List[User]:
        with db_cursor() as cur:
            cur.execute(
                _SELECT + "WHERE role = %s AND deleted_at IS NULL ORDER BY full_name",
                (role,),
            )
            return [_row_to_user(row) for row in cur.fetchall()]

    def get_all_active(self) -> List[User]:
        with db_cursor() as cur:
            cur.execute(
                _SELECT + "WHERE is_active = TRUE AND deleted_at IS NULL ORDER BY role, full_name"
            )
            return [_row_to_user(row) for row in cur.fetchall()]

    def update_profile(
        self,
        user_id: int,
        full_name: str,
        age: Optional[int],
        target_systolic: int,
        target_diastolic: int,
        target_pulse: int,
    ) -> None:
        with db_cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET full_name = %s, age = %s,
                    target_systolic = %s, target_diastolic = %s, target_pulse = %s
                WHERE id = %s
                """,
                (full_name, age, target_systolic, target_diastolic, target_pulse, user_id),
            )

    def set_active(self, user_id: int, is_active: bool) -> None:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE users SET is_active = %s WHERE id = %s",
                (is_active, user_id),
            )

    def reset_password(self, user_id: int, new_password: str) -> None:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (_hash_password(new_password), user_id),
            )

    def soft_delete(self, user_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s",
                (user_id,),
            )
