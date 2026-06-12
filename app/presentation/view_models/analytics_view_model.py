"""Analytics ViewModel - for analytics page with correlation."""
from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List
import logging

from PyQt6.QtCore import pyqtSignal

from app.presentation.view_models.base_view_model import BaseViewModel
from app.application.services import AnalysisService, MonitoringService
from app.application.dto import AnalysisResultDTO, MeasurementDTO, DateRangeDTO
from app.domain.entities import UserORM, MeasurementORM
from app.repositories import MeasurementRepositoryORM
from sqlalchemy.orm import Session

_logger = logging.getLogger(__name__)


class AnalyticsViewModel(BaseViewModel):
    """
    ViewModel for Analytics page.
    
    Displays:
    - Statistical summary
    - Pearson correlation (diploma formula 3.2)
    - Charts data
    - Recommendations
    """
    
    # Signals
    analysis_result_changed = pyqtSignal(object)  # AnalysisResultDTO
    correlation_result_changed = pyqtSignal(object)  # CorrelationResultDTO or None
    chart_data_changed = pyqtSignal(object)  # Dict with chart data
    period_changed = pyqtSignal(str)  # Period description
    
    def __init__(
        self,
        db: Session,
        current_user: UserORM,
        analysis_service: AnalysisService,
        monitoring_service: MonitoringService,
        measurement_repo: MeasurementRepositoryORM,
    ):
        super().__init__()
        self._db = db
        self._current_user = current_user
        self._analysis_service = analysis_service
        self._monitoring_service = monitoring_service
        self._measurement_repo = measurement_repo
        
        # State
        self._analysis_result: Optional[AnalysisResultDTO] = None
        self._period_days = 30
        self._chart_data: Dict[str, Any] = {}
    
    def analyze(self, days: int = 30):
        """Run analysis for period."""
        self._period_days = days
        self.safe_execute(self._run_analysis, "Analysis failed")
    
    def _run_analysis(self):
        """Internal analysis."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self._period_days)
        
        # Load measurements
        measurements = self._measurement_repo.get_by_user_and_date_range(
            self._current_user.id, start_date, end_date
        )
        
        # Run analysis
        self._analysis_result = self._analysis_service.analyze_measurements(
            patient_id=self._current_user.id,
            measurements=measurements,
        )
        
        # Prepare chart data
        self._prepare_chart_data(measurements)
        
        # Emit signals
        self.analysis_result_changed.emit(self._analysis_result)
        if self._analysis_result and self._analysis_result.bp_weather_correlation:
            self.correlation_result_changed.emit(self._analysis_result.bp_weather_correlation)
        self.chart_data_changed.emit(self._chart_data)
        
        period_text = f"За останні {self._period_days} днів"
        if self._period_days == 7:
            period_text = "За останній тиждень"
        elif self._period_days == 30:
            period_text = "За останній місяць"
        self.period_changed.emit(period_text)
        
        _logger.info(f"Analysis completed for user {self._current_user.id}, {len(measurements)} measurements")
    
    def _prepare_chart_data(self, measurements: List[MeasurementORM]):
        """Prepare data for charts."""
        if not measurements:
            self._chart_data = {}
            return
        
        # Sort by date
        sorted_measurements = sorted(measurements, key=lambda m: m.measured_at or datetime.min)
        
        self._chart_data = {
            "dates": [m.measured_at.isoformat() for m in sorted_measurements if m.measured_at],
            "systolic": [m.systolic for m in sorted_measurements],
            "diastolic": [m.diastolic for m in sorted_measurements],
            "pulse": [m.pulse for m in sorted_measurements if m.pulse],
            "pressure": [
                m.weather_snapshot.pressure_mmhg if m.weather_snapshot else None
                for m in sorted_measurements
            ],
        }
    
    def export_csv(self, file_path: str):
        """Export data to CSV."""
        def _export():
            # Would implement CSV export
            _logger.info(f"Exporting to {file_path}")
        
        self.safe_execute(_export, "Export failed")
    
    # Properties
    @property
    def analysis_result(self) -> Optional[AnalysisResultDTO]:
        return self._analysis_result
    
    @property
    def chart_data(self) -> Dict[str, Any]:
        return self._chart_data
    
    @property
    def has_correlation(self) -> bool:
        return (
            self._analysis_result is not None 
            and self._analysis_result.bp_weather_correlation is not None
        )
    
    @property
    def correlation_coefficient(self) -> Optional[float]:
        if self._analysis_result and self._analysis_result.bp_weather_correlation:
            return self._analysis_result.bp_weather_correlation.correlation_coefficient
        return None
    
    @property
    def recommendations(self) -> List[str]:
        if self._analysis_result:
            return self._analysis_result.recommendations
        return []
