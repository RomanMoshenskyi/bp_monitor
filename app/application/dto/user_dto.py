"""User DTOs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities import UserRole


@dataclass
class UserDTO:
    """User data transfer object."""
    id: int
    name: str
    email: str
    role: UserRole
    is_verified: bool
    specialization: Optional[str] = None
    primary_doctor_id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class UserCreateDTO:
    """DTO for creating new user."""
    name: str
    email: str
    password: str
    role: UserRole = UserRole.PATIENT
    specialization: Optional[str] = None


@dataclass
class UserUpdateDTO:
    """DTO for updating user."""
    name: Optional[str] = None
    email: Optional[str] = None
    specialization: Optional[str] = None
    primary_doctor_id: Optional[int] = None
    is_verified: Optional[bool] = None
