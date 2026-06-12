"""Recommendation DTOs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities import SeverityLevel


@dataclass
class RecommendationDTO:
    """Recommendation data transfer object."""
    id: int
    patient_id: int
    measurement_id: Optional[int]
    severity: SeverityLevel
    category: Optional[str]
    message: str
    is_read: bool
    is_acknowledged: bool
    created_at: datetime


@dataclass
class RecommendationCreateDTO:
    """DTO for creating recommendation."""
    patient_id: int
    measurement_id: Optional[int]
    severity: SeverityLevel
    category: str
    message: str
