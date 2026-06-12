"""Report DTOs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from app.domain.entities import ReportFormat, ReportStatus


@dataclass
class ReportDTO:
    """Report data transfer object."""
    id: int
    patient_id: int
    period_start: date
    period_end: date
    file_format: ReportFormat
    file_path: Optional[str]
    file_size: Optional[int]
    status: ReportStatus
    title: Optional[str]
    description: Optional[str]
    generated_at: Optional[datetime]
    created_at: datetime


@dataclass
class ReportCreateDTO:
    """DTO for creating report."""
    patient_id: int
    period_start: date
    period_end: date
    file_format: ReportFormat
    title: Optional[str] = None
    description: Optional[str] = None
    generated_by: Optional[int] = None  # Doctor ID or None for self-generated
