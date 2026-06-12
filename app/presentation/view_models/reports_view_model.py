"""Reports ViewModel - for generating health reports."""
from __future__ import annotations

from typing import List, Optional
from datetime import date

from PyQt6.QtCore import pyqtSignal

from app.presentation.view_models.base_view_model import BaseViewModel
from app.domain.entities import UserORM, ReportORM, ReportFormat, ReportStatus


class ReportsViewModel(BaseViewModel):
    """
    ViewModel for Reports page.
    
    Handles:
    - List of generated reports
    - Generate new report
    - Download report
    - View report metadata
    """
    
    # Signals
    reports_changed = pyqtSignal(list)  # List[ReportORM]
    report_generated = pyqtSignal(bool, str)  # success, message
    generation_progress = pyqtSignal(int)  # percentage
    
    def __init__(self, current_user: UserORM):
        super().__init__()
        self._current_user = current_user
        self._reports: List[ReportORM] = []
    
    def load_reports(self):
        """Load all reports for current user."""
        def _load():
            self._reports = []
            self.reports_changed.emit(self._reports)
        
        self.safe_execute(_load, "Failed to load reports")
    
    def generate_report(
        self,
        title: str,
        period_start: date,
        period_end: date,
        file_format: str = "pdf",
        description: str = ""
    ):
        """Generate new health report."""
        def _generate():
            # Implementation would use ReportService
            self.generation_progress.emit(50)
            # ... generation logic ...
            self.generation_progress.emit(100)
            self.report_generated.emit(True, "Звіт успішно згенеровано")
            self.load_reports()
        
        self.safe_execute(_generate, "Failed to generate report")
    
    def delete_report(self, report_id: int):
        """Delete report."""
        def _delete():
            # Implementation would use repository
            self.load_reports()
        
        self.safe_execute(_delete, "Failed to delete report")
    
    def get_format_options(self) -> List[tuple]:
        """Get available report formats."""
        return [
            ("pdf", "PDF Document"),
            ("csv", "CSV Spreadsheet"),
            ("json", "JSON Data"),
        ]
    
    @property
    def reports(self) -> List[ReportORM]:
        return self._reports
