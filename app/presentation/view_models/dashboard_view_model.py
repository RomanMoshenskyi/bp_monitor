"""Dashboard ViewModel - for main dashboard page."""
from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
import logging

from PyQt6.QtCore import pyqtSignal

from app.presentation.view_models.base_view_model import BaseViewModel
from app.application.services import MonitoringService, AnalysisService
from app.application.dto import MeasurementDTO, AnalysisResultDTO
from app.domain.entities import UserORM, UserRole

_logger = logging.getLogger(__name__)


class DashboardViewModel(BaseViewModel):
    """
    ViewModel for Dashboard page.
    
    Displays:
    - Latest measurement
    - Daily summary stats
    - Recent activity
    - Unread recommendations count
    """
    
    # Specific signals for dashboard
    latest_measurement_changed = pyqtSignal(object)  # MeasurementDTO
    stats_changed = pyqtSignal(object)  # Dict with stats
    recommendations_count_changed = pyqtSignal(int)
    
    def __init__(
        self,
        current_user: UserORM,
        monitoring_service: MonitoringService,
        analysis_service: AnalysisService,
    ):
        super().__init__()
        self._current_user = current_user
        self._monitoring_service = monitoring_service
        self._analysis_service = analysis_service
        
        # State
        self._latest_measurement: Optional[MeasurementDTO] = None
        self._daily_stats: Dict[str, Any] = {}
        self._unread_recommendations_count = 0
        self._recent_measurements: List[MeasurementDTO] = []
    
    def load(self):
        """Load dashboard data."""
        self.safe_execute(self._load_data, "Failed to load dashboard")
    
    def _load_data(self):
        """Internal data loading."""
        user_id = self._current_user.id
        
        # Get latest measurement
        self._latest_measurement = self._monitoring_service.get_latest_measurement(user_id)
        
        # Get recent measurements (last 7 days)
        from app.application.dto import DateRangeDTO
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        self._recent_measurements = self._monitoring_service.get_history(
            user_id,
            DateRangeDTO(start_date=start_date, end_date=end_date),
            self._current_user
        )
        
        # Calculate stats
        if self._recent_measurements:
            self._calculate_stats()
        
        # Emit signals
        if self._latest_measurement:
            self.latest_measurement_changed.emit(self._latest_measurement)
        self.stats_changed.emit(self._daily_stats)
        
        _logger.info(f"Dashboard loaded for user {user_id}")
    
    def _calculate_stats(self):
        """Calculate statistics for dashboard."""
        measurements = self._recent_measurements
        if not measurements:
            return
        
        systolics = [m.systolic for m in measurements]
        diastolics = [m.diastolic for m in measurements]
        
        self._daily_stats = {
            "total_measurements": len(measurements),
            "avg_systolic": sum(systolics) / len(systolics),
            "avg_diastolic": sum(diastolics) / len(diastolics),
            "latest_status": self._latest_measurement.pressure_status if self._latest_measurement else "unknown",
        }
    
    # Properties for View binding
    @property
    def latest_measurement(self) -> Optional[MeasurementDTO]:
        return self._latest_measurement
    
    @property
    def daily_stats(self) -> Dict[str, Any]:
        return self._daily_stats
    
    @property
    def current_user_name(self) -> str:
        return self._current_user.name
    
    @property
    def is_doctor(self) -> bool:
        return self._current_user.role == UserRole.DOCTOR
    
    @property
    def is_admin(self) -> bool:
        return self._current_user.role == UserRole.ADMIN
