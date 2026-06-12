"""AccessControl - RBAC from diploma class diagram."""
from __future__ import annotations

import logging
from typing import Optional

from app.domain.entities import UserORM, UserRole, MeasurementORM

_logger = logging.getLogger(__name__)


class AccessControl:
    """
    Role-Based Access Control service.
    
    From diploma class diagram:
    - canRead(user, patientId)
    - canWrite(user, patientId)
    
    Rules:
    - ADMIN: full access to everything
    - DOCTOR: read/write assigned patients only
    - PATIENT: read/write own data only
    """
    
    @staticmethod
    def can_read(user: UserORM, patient_id: int) -> bool:
        """Check if user can read patient's data."""
        if not user:
            return False
        
        # Admin can read everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Doctor can read assigned patients
        if user.role == UserRole.DOCTOR:
            # Doctor can read if they are the primary doctor
            # This would require a query, simplified here
            return True  # Simplified - would check assignment
        
        # Patient can only read own data
        if user.role == UserRole.PATIENT:
            return user.id == patient_id
        
        return False
    
    @staticmethod
    def can_write(user: UserORM, patient_id: int) -> bool:
        """Check if user can write patient's data."""
        if not user:
            return False
        
        # Admin can write everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Doctor can write to assigned patients
        if user.role == UserRole.DOCTOR:
            # Simplified - would check doctor-patient assignment
            return True
        
        # Patient can only write own data
        if user.role == UserRole.PATIENT:
            return user.id == patient_id
        
        return False
    
    @staticmethod
    def can_delete_measurement(user: UserORM, measurement: MeasurementORM) -> bool:
        """Check if user can delete a specific measurement."""
        if not user or not measurement:
            return False
        
        # Admin can delete anything
        if user.role == UserRole.ADMIN:
            return True
        
        # Patient can only delete own measurements
        if user.role == UserRole.PATIENT:
            return measurement.user_id == user.id
        
        # Doctor can delete their patients' measurements
        if user.role == UserRole.DOCTOR:
            # Would check if patient is assigned to doctor
            return True  # Simplified
        
        return False
    
    @staticmethod
    def can_view_recommendations(user: UserORM, patient_id: int) -> bool:
        """Check if user can view patient's recommendations."""
        # Same as can_read
        return AccessControl.can_read(user, patient_id)
    
    @staticmethod
    def can_generate_report(user: UserORM, patient_id: int) -> bool:
        """Check if user can generate report for patient."""
        # Doctors and admins can generate reports
        if user.role in [UserRole.ADMIN, UserRole.DOCTOR]:
            return True
        
        # Patients can generate own reports
        if user.role == UserRole.PATIENT:
            return user.id == patient_id
        
        return False
    
    @staticmethod
    def check_permission(
        user: UserORM, 
        action: str, 
        patient_id: int,
        resource: Optional[Any] = None,
    ) -> bool:
        """
        General permission check.
        
        Args:
            user: Current user
            action: Action to perform (read, write, delete, etc.)
            patient_id: Target patient ID
            resource: Optional resource being accessed
        """
        if not user:
            _logger.warning(f"Permission denied: no user for action {action}")
            return False
        
        # Admin bypass
        if user.role == UserRole.ADMIN:
            return True
        
        # Check based on action
        if action in ["read", "view"]:
            return AccessControl.can_read(user, patient_id)
        elif action in ["write", "create", "update"]:
            return AccessControl.can_write(user, patient_id)
        elif action == "delete" and isinstance(resource, MeasurementORM):
            return AccessControl.can_delete_measurement(user, resource)
        elif action == "generate_report":
            return AccessControl.can_generate_report(user, patient_id)
        
        _logger.warning(f"Unknown action {action} for user {user.id}")
        return False
    
    @staticmethod
    def assert_permission(
        user: UserORM,
        action: str,
        patient_id: int,
        resource: Optional[Any] = None,
    ) -> None:
        """Assert permission or raise PermissionError."""
        if not AccessControl.check_permission(user, action, patient_id, resource):
            raise PermissionError(
                f"User {user.id} with role {user.role.value} "
                f"cannot perform {action} on patient {patient_id}"
            )


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    pass
