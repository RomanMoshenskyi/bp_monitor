"""User Repository - ORM version for SQLAlchemy."""
from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import UserORM, UserRole


class UserRepositoryORM:
    """Repository for UserORM operations."""
    
    def __init__(self, db: Session):
        self._db = db
    
    def get_by_id(self, user_id: int) -> Optional[UserORM]:
        """Get user by ID."""
        return self._db.get(UserORM, user_id)
    
    def get_by_email(self, email: str) -> Optional[UserORM]:
        """Get user by email (unique)."""
        stmt = select(UserORM).where(UserORM.email == email.lower())
        return self._db.execute(stmt).scalar_one_or_none()
    
    def get_by_role(self, role: UserRole) -> List[UserORM]:
        """Get all users with specific role."""
        stmt = select(UserORM).where(UserORM.role == role).order_by(UserORM.name)
        return list(self._db.execute(stmt).scalars().all())
    
    def get_all_verified(self) -> List[UserORM]:
        """Get all verified users."""
        stmt = select(UserORM).where(UserORM.is_verified == True).order_by(UserORM.created_at)
        return list(self._db.execute(stmt).scalars().all())
    
    def get_patients_by_doctor(self, doctor_id: int) -> List[UserORM]:
        """Get all patients assigned to a doctor."""
        stmt = select(UserORM).where(
            UserORM.primary_doctor_id == doctor_id,
            UserORM.role == UserRole.PATIENT
        ).order_by(UserORM.name)
        return list(self._db.execute(stmt).scalars().all())
    
    def create(self, user: UserORM) -> UserORM:
        """Create new user."""
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
    
    def update(self, user: UserORM) -> UserORM:
        """Update user."""
        self._db.merge(user)
        self._db.commit()
        self._db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """Delete user."""
        user = self.get_by_id(user_id)
        if user:
            self._db.delete(user)
            self._db.commit()
            return True
        return False
    
    def set_verified(self, user_id: int, verified: bool = True) -> bool:
        """Set user verification status."""
        user = self.get_by_id(user_id)
        if user:
            user.is_verified = verified
            self._db.commit()
            return True
        return False
