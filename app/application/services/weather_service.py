"""WeatherService - from diploma class diagram."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.entities import WeatherSnapshotORM
from app.repositories import WeatherRepository
from app.weather import fetch_atmospheric_pressure_mmhg  # Existing function

_logger = logging.getLogger(__name__)


class WeatherService:
    """
    Weather data service.
    
    From diploma class diagram: WeatherServiceClient.getPressure(location, time)
    
    Integrates with existing app.weather module and new ORM.
    """
    
    def __init__(
        self,
        db: Session,
        weather_repo: WeatherRepository,
        cache_minutes: int = 30,
    ):
        self._db = db
        self._weather_repo = weather_repo
        self._cache_minutes = cache_minutes
    
    def get_pressure_for_measurement(
        self,
        city: str,
        measurement_time: datetime,
    ) -> Optional[WeatherSnapshotORM]:
        """
        Get or fetch weather data for a measurement.
        
        1. Check if we have recent snapshot in DB
        2. If not, fetch from API
        3. Save to DB for future use
        """
        # Try to find existing snapshot
        existing = self._weather_repo.get_by_city_and_time(
            city, measurement_time, window_minutes=self._cache_minutes
        )
        
        if existing:
            _logger.debug(f"Found cached weather for {city} at {measurement_time}")
            return existing
        
        # Fetch from API
        _logger.info(f"Fetching weather for {city}")
        pressure_mmhg = fetch_atmospheric_pressure_mmhg(city)
        
        if pressure_mmhg is None:
            _logger.warning(f"Could not fetch weather for {city}")
            return None
        
        # Convert to hPa for storage
        pressure_hpa = pressure_mmhg / 0.75006
        
        # Create snapshot
        snapshot = WeatherSnapshotORM(
            city=city,
            latitude=0.0,  # Would get from geocoding
            longitude=0.0,
            pressure_hpa=pressure_hpa,
            pressure_mmhg=pressure_mmhg,
            recorded_at=measurement_time,
        )
        
        # Save
        saved = self._weather_repo.create(snapshot)
        _logger.info(f"Saved weather snapshot {saved.id} for {city}")
        
        return saved
    
    def get_current_pressure(self, city: str = "Київ") -> Optional[int]:
        """Get current atmospheric pressure (convenience method)."""
        snapshot = self.get_pressure_for_measurement(city, datetime.utcnow())
        return snapshot.pressure_mmhg if snapshot else None
    
    def get_cached_pressure(
        self,
        city: str,
        max_age_minutes: int = 60,
    ) -> Optional[WeatherSnapshotORM]:
        """Get cached pressure if not too old."""
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        # Get latest for city
        latest = self._weather_repo.get_latest_for_city(city)
        
        if latest and latest.recorded_at >= cutoff:
            return latest
        
        return None
    
    def prefetch_weather(self, cities: list[str]) -> dict[str, Optional[int]]:
        """Pre-fetch weather for multiple cities."""
        results = {}
        for city in cities:
            try:
                pressure = self.get_current_pressure(city)
                results[city] = pressure
            except Exception as e:
                _logger.error(f"Failed to fetch weather for {city}: {e}")
                results[city] = None
        return results
