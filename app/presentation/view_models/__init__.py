"""ViewModels for MVVM pattern - presentation layer."""
from __future__ import annotations

from .base_view_model import BaseViewModel
from .dashboard_view_model import DashboardViewModel
from .measurements_view_model import MeasurementsViewModel
from .analytics_view_model import AnalyticsViewModel
from .medications_view_model import MedicationsViewModel
from .activities_view_model import ActivitiesViewModel
from .thresholds_view_model import ThresholdsViewModel
from .reports_view_model import ReportsViewModel
from .recommendations_view_model import RecommendationsViewModel
from .doctor_reports_view_model import DoctorReportsViewModel
from .prescriptions_view_model import PrescriptionsViewModel
from .ai_insights_view_model import AIInsightsViewModel

__all__ = [
    "BaseViewModel",
    "DashboardViewModel",
    "MeasurementsViewModel",
    "AnalyticsViewModel",
    "MedicationsViewModel",
    "ActivitiesViewModel",
    "ThresholdsViewModel",
    "ReportsViewModel",
    "RecommendationsViewModel",
    "DoctorReportsViewModel",
    "PrescriptionsViewModel",
    "AIInsightsViewModel",
]
