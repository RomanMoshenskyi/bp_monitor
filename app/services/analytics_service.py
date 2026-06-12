from __future__ import annotations

from typing import List, Optional, Sequence

from ..analytics import (
    correlation_atmospheric,
    filter_by_days,
    generate_recommendations,
    latest_measurement,
    pressure_status,
    summary,
)
from ..models import Measurement


class AnalyticsService:
    """Thin facade over analytics functions; keeps UI decoupled from analytics module."""

    def get_summary(self, measurements: Sequence[Measurement]) -> dict:
        return summary(measurements)

    def get_correlation(self, measurements: Sequence[Measurement]) -> Optional[float]:
        return correlation_atmospheric(measurements)

    def get_recommendations(self, measurements: Sequence[Measurement]) -> List[str]:
        return generate_recommendations(measurements)

    def filter_by_period(
        self, measurements: Sequence[Measurement], days: Optional[int]
    ) -> List[Measurement]:
        if days is None:
            return list(measurements)
        return filter_by_days(measurements, days)

    def get_latest(self, measurements: Sequence[Measurement]) -> Optional[Measurement]:
        return latest_measurement(measurements)

    def get_pressure_status(self, systolic: int, diastolic: int) -> str:
        return pressure_status(systolic, diastolic)
