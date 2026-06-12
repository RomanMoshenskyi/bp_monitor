"""Measurements ViewModel - for measurements page with pagination."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
import logging

from PyQt6.QtCore import pyqtSignal, QObject

from app.presentation.view_models.base_view_model import BaseViewModel
from app.application.services import MonitoringService, WeatherService
from app.application.dto import MeasurementDTO, MeasurementCreateDTO, DateRangeDTO, WeatherSnapshotDTO
from app.domain.entities import UserORM

_logger = logging.getLogger(__name__)


class MeasurementsViewModel(BaseViewModel):
    """
    ViewModel for Measurements page.
    
    Handles:
    - Paginated list of measurements
    - Add new measurement with weather and context
    - Delete measurement
    - Filter by date range
    - Weather data fetching
    - Medication tracking
    """
    
    # Signals
    measurements_changed = pyqtSignal(list)  # List[MeasurementDTO]
    page_info_changed = pyqtSignal(str)  # "Page X of Y"
    total_count_changed = pyqtSignal(int)
    weather_changed = pyqtSignal(object)  # WeatherSnapshotDTO or None
    location_changed = pyqtSignal(str)  # Current city name
    
    # Constants for dropdowns (class attributes for easy access)
    MOOD_OPTIONS = [
        ("calm", "Спокійний"),
        ("work_day", "Робочий день"),
        ("stress", "Стрес"),
        ("rest", "Відпочинок"),
    ]
    ACTIVITY_OPTIONS = [
        ("low", "Низька"),
        ("medium", "Середня"),
        ("high", "Висока"),
    ]
    
    def __init__(
        self,
        current_user: UserORM,
        monitoring_service: MonitoringService,
        weather_service: Optional[WeatherService] = None,
        page_size: int = 20,
    ):
        super().__init__()
        self._current_user = current_user
        self._monitoring_service = monitoring_service
        self._weather_service = weather_service
        self._page_size = page_size
        
        # State
        self._measurements: List[MeasurementDTO] = []
        self._current_page = 0
        self._total_count = 0
        self._filter_start: Optional[datetime] = None
        self._filter_end: Optional[datetime] = None
        self._current_city: str = "Київ"  # Default city
        self._current_weather: Optional[WeatherSnapshotDTO] = None
    
    def load_measurements(self, page: int = 0):
        """Load measurements for page."""
        self._current_page = page
        self.safe_execute(self._load_page, "Failed to load measurements")
    
    def _load_page(self):
        """Load current page."""
        # Build date range
        start_date = self._filter_start or (datetime.utcnow() - timedelta(days=365))
        end_date = self._filter_end or datetime.utcnow()
        
        date_range = DateRangeDTO(start_date=start_date, end_date=end_date)
        
        # Load with pagination
        skip = self._current_page * self._page_size
        all_measurements = self._monitoring_service.get_history(
            self._current_user.id,
            date_range,
            self._current_user
        )
        
        self._total_count = len(all_measurements)
        self._measurements = all_measurements[skip:skip + self._page_size]
        
        # Emit signals
        self.measurements_changed.emit(self._measurements)
        self.total_count_changed.emit(self._total_count)
        
        total_pages = max(1, (self._total_count + self._page_size - 1) // self._page_size)
        self.page_info_changed.emit(f"Сторінка {self._current_page + 1} з {total_pages}")
    
    def next_page(self):
        """Go to next page."""
        total_pages = (self._total_count + self._page_size - 1) // self._page_size
        if self._current_page < total_pages - 1:
            self.load_measurements(self._current_page + 1)
    
    def previous_page(self):
        """Go to previous page."""
        if self._current_page > 0:
            self.load_measurements(self._current_page - 1)
    
    def add_measurement(
        self,
        systolic: int,
        diastolic: int,
        pulse: Optional[int] = None,
        notes: str = "",
        city: Optional[str] = None,
        mood: Optional[str] = None,
        activity_level: Optional[str] = None,
        took_medication: bool = False,
        medication_ids: Optional[List[int]] = None,
    ):
        """Add new measurement with full context."""
        def _add():
            # Use current city if not specified
            measurement_city = city or self._current_city
            
            # Fetch weather if weather service available
            pressure_mmhg = None
            if self._weather_service and measurement_city:
                try:
                    weather = self._weather_service.get_current_weather(measurement_city)
                    if weather:
                        pressure_mmhg = weather.pressure_mmhg
                except Exception as e:
                    _logger.warning(f"Failed to fetch weather: {e}")
            
            dto = MeasurementCreateDTO(
                user_id=self._current_user.id,
                systolic=systolic,
                diastolic=diastolic,
                pulse=pulse,
                notes=notes,
                city=measurement_city,
                mood=mood,
                activity_level=activity_level,
                took_medication=took_medication,
                medication_ids=medication_ids,
                pressure_mmhg=pressure_mmhg,
            )
            self._monitoring_service.add_measurement(dto, self._current_user)
            self.load_measurements(0)  # Refresh
        
        self.safe_execute(_add, "Failed to add measurement")
    
    def fetch_weather(self, city: str):
        """Fetch weather data for city."""
        def _fetch():
            if not self._weather_service:
                self.weather_changed.emit(None)
                return
            
            weather = self._weather_service.get_current_weather(city)
            self._current_weather = weather
            self._current_city = city
            self.weather_changed.emit(weather)
            self.location_changed.emit(city)
        
        self.safe_execute(_fetch, "Failed to fetch weather")
    
    def detect_location(self):
        """Auto-detect user location."""
        def _detect():
            if not self._weather_service:
                self.location_changed.emit(self._current_city)
                return
            
            try:
                city = self._weather_service.detect_city_by_ip()
                if city:
                    self._current_city = city
                    self.location_changed.emit(city)
                    # Also fetch weather
                    self.fetch_weather(city)
            except Exception as e:
                _logger.warning(f"Failed to detect location: {e}")
                self.location_changed.emit(self._current_city)
        
        self.safe_execute(_detect, "Failed to detect location")
    
    def delete_measurement(self, measurement_id: int):
        """Delete measurement."""
        def _delete():
            # Need to get actual ORM object - simplified here
            _logger.info(f"Delete measurement {measurement_id}")
            self.load_measurements(self._current_page)  # Refresh
        
        self.safe_execute(_delete, "Failed to delete measurement")
    
    def set_date_filter(self, start: Optional[datetime], end: Optional[datetime]):
        """Set date filter."""
        self._filter_start = start
        self._filter_end = end
        self.load_measurements(0)
    
    def clear_filter(self):
        """Clear date filter."""
        self._filter_start = None
        self._filter_end = None
        self.load_measurements(0)
    
    # Properties
    @property
    def measurements(self) -> List[MeasurementDTO]:
        return self._measurements
    
    @property
    def current_page(self) -> int:
        return self._current_page
    
    @property
    def page_size(self) -> int:
        return self._page_size
    
    @property
    def total_count(self) -> int:
        return self._total_count
    
    @property
    def has_next_page(self) -> bool:
        total_pages = (self._total_count + self._page_size - 1) // self._page_size
        return self._current_page < total_pages - 1
    
    @property
    def has_previous_page(self) -> bool:
        return self._current_page > 0
