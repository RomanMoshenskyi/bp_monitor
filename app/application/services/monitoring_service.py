"""MonitoringService - central coordinator from diploma class diagram."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, List, Optional
import logging

from sqlalchemy.orm import Session

from app.domain.entities import (
    MeasurementORM, UserORM, WeatherSnapshotORM, 
    DailySummaryORM, RecommendationORM, SeverityLevel,
    UserRole
)
from app.application.dto import (
    MeasurementDTO, MeasurementCreateDTO,
    AnalysisResultDTO, DateRangeDTO
)
from app.repositories import (
    MeasurementRepositoryORM,
    UserRepositoryORM,
    WeatherRepository,
)

_logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Central monitoring coordinator - main entry point for business logic.
    
    From diploma class diagram:
    - addMeasurement(data)
    - getHistory(userId, period)
    - getReports(userId, period)
    """
    
    def __init__(
        self,
        db: Session,
        measurement_repo: MeasurementRepositoryORM,
        user_repo: UserRepositoryORM,
        weather_repo: WeatherRepository,
        analysis_service: Optional[Any] = None,
        audit_service: Optional[Any] = None,
    ):
        self._db = db
        self._measurement_repo = measurement_repo
        self._user_repo = user_repo
        self._weather_repo = weather_repo
        self._analysis_service = analysis_service
        self._audit_service = audit_service
    
    def add_measurement(
        self, 
        dto: MeasurementCreateDTO, 
        current_user: UserORM,
        city: str = "Київ"
    ) -> MeasurementDTO:
        """
        Add new measurement with weather data.
        
        From diploma: addMeasurement(data) with automatic weather correlation.
        """
        # Authorization check
        if current_user.role == UserRole.PATIENT and dto.user_id != current_user.id:
            raise PermissionError("Patients can only add their own measurements")
        
        # Fetch weather if not already linked
        weather_snapshot = None
        if dto.measured_at is None:
            dto.measured_at = datetime.utcnow()
        
        # Try to find existing weather snapshot
        weather_snapshot = self._weather_repo.get_by_city_and_time(
            city, dto.measured_at, window_minutes=30
        )
        
        if not weather_snapshot and self._analysis_service:
            # Would fetch from weather service here
            _logger.info(f"Weather snapshot not found for {city}, would fetch")
        
        # Create measurement entity
        measurement = MeasurementORM(
            user_id=dto.user_id,
            systolic=dto.systolic,
            diastolic=dto.diastolic,
            pulse=dto.pulse,
            measured_at=dto.measured_at,
            latitude=dto.latitude,
            longitude=dto.longitude,
            notes=dto.notes,
            weather_snapshot_id=weather_snapshot.id if weather_snapshot else None,
        )
        
        # Save
        saved = self._measurement_repo.create(measurement)
        
        # Audit log
        if self._audit_service:
            self._audit_service.log(
                user_id=current_user.id,
                action="measurement_created",
                entity_type="measurement",
                entity_id=saved.id,
                details={
                    "systolic": saved.systolic,
                    "diastolic": saved.diastolic,
                    "weather_linked": weather_snapshot is not None,
                }
            )
        
        _logger.info(f"Measurement {saved.id} created for user {dto.user_id}")
        
        return self._to_dto(saved)
    
    def get_history(
        self, 
        user_id: int, 
        date_range: DateRangeDTO,
        current_user: UserORM
    ) -> List[MeasurementDTO]:
        """Get measurement history for a user."""
        # Access control
        if current_user.role == UserRole.PATIENT and user_id != current_user.id:
            raise PermissionError("Access denied")
        
        measurements = self._measurement_repo.get_by_user_and_date_range(
            user_id, date_range.start_date, date_range.end_date
        )
        
        return [self._to_dto(m) for m in measurements]
    
    def get_latest_measurement(self, user_id: int) -> Optional[MeasurementDTO]:
        """Get latest measurement for user."""
        measurement = self._measurement_repo.get_latest_for_user(user_id)
        return self._to_dto(measurement) if measurement else None
    
    def delete_measurement(
        self, 
        measurement_id: int, 
        current_user: UserORM
    ) -> bool:
        """Delete a measurement."""
        measurement = self._measurement_repo.get_by_id(measurement_id)
        if not measurement:
            return False
        
        # Authorization
        if current_user.role == UserRole.PATIENT:
            if measurement.user_id != current_user.id:
                raise PermissionError("Can only delete own measurements")
        
        deleted = self._measurement_repo.delete(measurement_id)
        
        if deleted and self._audit_service:
            self._audit_service.log(
                user_id=current_user.id,
                action="measurement_deleted",
                entity_type="measurement",
                entity_id=measurement_id,
            )
        
        return deleted
    
    def _to_dto(self, measurement: MeasurementORM) -> MeasurementDTO:
        """Convert ORM to DTO."""
        return MeasurementDTO(
            id=measurement.id,
            user_id=measurement.user_id,
            systolic=measurement.systolic,
            diastolic=measurement.diastolic,
            pulse=measurement.pulse,
            measured_at=measurement.measured_at,
            latitude=measurement.latitude,
            longitude=measurement.longitude,
            notes=measurement.notes,
            weather_snapshot_id=measurement.weather_snapshot_id,
        )


# Type hint for circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.application.services.analysis_service import AnalysisService
    from app.application.services.audit_service import AuditService
