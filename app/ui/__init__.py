from .analytics_page import AnalyticsPage
from .dashboard_page import DashboardPage
from .measurements_page import MeasurementsPage
from .settings_page import SettingsPage
from .doctor_medical_reports_page import DoctorMedicalReportsPage
from .doctor_prescriptions_page import DoctorPrescriptionsPage
from .patient_prescriptions_page import PatientPrescriptionsPage
from .ai_insights_page import AIInsightsPage
from .admin_pages import (
    AdminDashboardPage, AdminAuditLogPage, AdminMedicationsPage,
    AdminPrescriptionsPage, AdminMeasurementsPage
)

__all__ = [
    "AnalyticsPage",
    "DashboardPage",
    "MeasurementsPage",
    "SettingsPage",
    "DoctorMedicalReportsPage",
    "DoctorPrescriptionsPage",
    "PatientPrescriptionsPage",
    "AIInsightsPage",
    "AdminDashboardPage",
    "AdminAuditLogPage",
    "AdminMedicationsPage",
    "AdminPrescriptionsPage",
    "AdminMeasurementsPage",
]
