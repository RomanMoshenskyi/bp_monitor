"""Weather ORM Models - WeatherSnapshot from diploma."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.orm.base import Base


class WeatherSnapshotORM(Base):
    """
    AtmosphericPressureSample entity from diploma diagram.
    
    Stores weather data at a specific time/location.
    Multiple measurements can reference the same snapshot.
    
    Attributes:
        id: Primary key
        city: City name (e.g., "Kyiv")
        latitude: Location latitude
        longitude: Location longitude
        pressure_hpa: Atmospheric pressure in hPa
        pressure_mmhg: Atmospheric pressure in mmHg
        temperature: Temperature in Celsius (optional)
        humidity: Humidity percentage (optional)
        recorded_at: When weather was recorded
    """
    __tablename__ = "weather_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Location info
    city = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Atmospheric pressure (both units for convenience)
    pressure_hpa = Column(Float, nullable=False)  # hectopascals
    pressure_mmhg = Column(Integer, nullable=False, index=True)  # mmHg
    
    # Optional weather data
    temperature = Column(Float, nullable=True)
    humidity = Column(Integer, nullable=True)  # 0-100%
    weather_description = Column(String(100), nullable=True)  # e.g., "clear sky"
    
    # When this weather snapshot was recorded
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # When this record was created in our DB
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    measurements = relationship("MeasurementORM", back_populates="weather_snapshot", lazy="dynamic")
    
    # Index for fast lookup by city + time (common query pattern)
    __table_args__ = (
        Index('ix_weather_city_recorded', 'city', 'recorded_at'),
    )
    
    def __repr__(self) -> str:
        return f"<WeatherSnapshotORM(id={self.id}, city={self.city}, {self.pressure_mmhg}mmHg)>"
    
    @classmethod
    def from_api_response(cls, city: str, data: dict) -> "WeatherSnapshotORM":
        """Create snapshot from Open-Meteo API response."""
        pressure_hpa = data.get("current", {}).get("surface_pressure")
        if pressure_hpa is None:
            raise ValueError("No surface_pressure in API response")
        
        # Convert hPa to mmHg (1 hPa = 0.75006 mmHg)
        pressure_mmhg = int(round(float(pressure_hpa) * 0.75006))
        
        return cls(
            city=city,
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
            pressure_hpa=float(pressure_hpa),
            pressure_mmhg=pressure_mmhg,
            temperature=data.get("current", {}).get("temperature_2m"),
            recorded_at=datetime.utcnow(),
        )
