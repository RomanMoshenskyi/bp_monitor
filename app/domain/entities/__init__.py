"""Domain entities package - ORM models from diploma."""
from __future__ import annotations

# Base models (3)
from app.domain.entities.user_orm import UserORM, UserRole
from app.domain.entities.measurement_orm import MeasurementORM
from app.domain.entities.weather_orm import WeatherSnapshotORM

# Extended models (8 more)
from app.domain.entities.medication_orm import MedicationORM, MedicationIntakeORM
from app.domain.entities.activity_orm import ActivityEventORM, ActivityType
from app.domain.entities.threshold_orm import ThresholdProfileORM
from app.domain.entities.daily_summary_orm import DailySummaryORM
from app.domain.entities.recommendation_orm import RecommendationORM, SeverityLevel
from app.domain.entities.audit_log_orm import AuditLogEntryORM
from app.domain.entities.report_orm import ReportORM, ReportFormat, ReportStatus
from app.domain.entities.doctor_report_orm import DoctorReportORM
from app.domain.entities.prescription_orm import PrescriptionORM, PrescriptionStatus

__all__ = [
    # Enums
    "UserRole",
    "ActivityType",
    "SeverityLevel",
    "ReportFormat",
    "ReportStatus",
    "PrescriptionStatus",
    # ORM Models (13 total)
    "UserORM",
    "MeasurementORM",
    "WeatherSnapshotORM",
    "MedicationORM",
    "MedicationIntakeORM",
    "ActivityEventORM",
    "ThresholdProfileORM",
    "DailySummaryORM",
    "RecommendationORM",
    "AuditLogEntryORM",
    "ReportORM",
    "DoctorReportORM",
    "PrescriptionORM",
]
