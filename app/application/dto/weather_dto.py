"""Weather DTOs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WeatherSnapshotDTO:
    """Weather snapshot data transfer object."""
    id: Optional[int]
    city: str
    latitude: float
    longitude: float
    pressure_hpa: float
    pressure_mmhg: int
    temperature: Optional[float]
    humidity: Optional[int]
    weather_description: Optional[str]
    recorded_at: datetime


@dataclass
class WeatherRequestDTO:
    """DTO for requesting weather data."""
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
