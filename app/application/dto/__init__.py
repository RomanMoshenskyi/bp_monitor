"""DTOs for data transfer between UI and Service layer."""
from __future__ import annotations

from .user_dto import UserDTO, UserCreateDTO, UserUpdateDTO
from .measurement_dto import MeasurementDTO, MeasurementCreateDTO, DateRangeDTO
from .weather_dto import WeatherSnapshotDTO
from .analysis_dto import MeasurementStatsDTO, AnalysisResultDTO, CorrelationResultDTO
from .recommendation_dto import RecommendationDTO, RecommendationCreateDTO
from .report_dto import ReportDTO, ReportCreateDTO

__all__ = [
    "UserDTO",
    "UserCreateDTO",
    "UserUpdateDTO",
    "MeasurementDTO",
    "MeasurementCreateDTO",
    "DateRangeDTO",
    "WeatherSnapshotDTO",
    "MeasurementStatsDTO",
    "AnalysisResultDTO",
    "CorrelationResultDTO",
    "RecommendationDTO",
    "RecommendationCreateDTO",
    "ReportDTO",
    "ReportCreateDTO",
]
