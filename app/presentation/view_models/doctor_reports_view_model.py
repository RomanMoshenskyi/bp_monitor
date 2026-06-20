"""DoctorReportsViewModel - ViewModel for doctor medical reports."""
from __future__ import annotations

from typing import List, Optional
from datetime import date
from pathlib import Path

from PyQt6.QtCore import pyqtSignal

from app.presentation.view_models.base_view_model import BaseViewModel
from app.domain.entities import UserORM
from app.application.dto import DoctorReportDTO, DoctorReportCreateDTO
from app.application.services import DoctorReportService


class DoctorReportsViewModel(BaseViewModel):
    """
    ViewModel for Doctor Medical Reports page.
    
    Handles:
    - Creating medical reports with full clinical data
    - Listing doctor's reports (private)
    - Signing reports
    - Generating and downloading HTML reports
    """
    
    # Signals
    reports_changed = pyqtSignal(list)  # List[DoctorReportDTO]
    report_created = pyqtSignal(bool, str)  # success, message
    report_signed = pyqtSignal(bool, str)  # success, message
    report_generated = pyqtSignal(bool, str, str)  # success, message, file_path
    
    def __init__(self, current_user: UserORM, db_session=None):
        super().__init__()
        self._current_user = current_user
        self._db_session = db_session
        self._service: Optional[DoctorReportService] = None
        self._reports: List[DoctorReportDTO] = []
        self._selected_patient_id: Optional[int] = None
        
        if db_session:
            self._service = DoctorReportService(db_session)
    
    def set_db_session(self, db_session):
        """Set database session (for initialization after login)."""
        self._db_session = db_session
        self._service = DoctorReportService(db_session)
    
    def set_selected_patient(self, patient_id: Optional[int]):
        """Set the currently selected patient."""
        self._selected_patient_id = patient_id
    
    def load_reports(self):
        """Load all reports created by current doctor."""
        def _load():
            if not self._service:
                self.reports_changed.emit([])
                return
            
            self._reports = self._service.list_doctor_reports(
                doctor_id=self._current_user.id,
                limit=100
            )
            self.reports_changed.emit(self._reports)
        
        self.safe_execute(_load, "Failed to load reports")
    
    def create_report(self, report_data: dict) -> Optional[DoctorReportDTO]:
        """
        Create a new medical report.
        
        Args:
            report_data: Dictionary with report fields
            
        Returns:
            Created report DTO or None
        """
        if not self._service:
            self.report_created.emit(False, "Service not available")
            return None
        
        if not self._selected_patient_id:
            self.report_created.emit(False, "No patient selected")
            return None
        
        def _create():
            # Build DTO from form data
            create_dto = DoctorReportCreateDTO(
                patient_id=self._selected_patient_id,
                doctor_id=self._current_user.id,
                report_date=report_data.get("report_date", date.today()),
                
                # Complaints and history
                chief_complaint=report_data.get("chief_complaint"),
                history_illness=report_data.get("history_illness"),
                history_life=report_data.get("history_life"),
                
                # Examination
                objective_exam=report_data.get("objective_exam"),
                general_condition=report_data.get("general_condition"),
                consciousness=report_data.get("consciousness"),
                body_temperature=report_data.get("body_temperature"),
                skin_condition=report_data.get("skin_condition"),
                
                # Vital signs
                heart_rate=report_data.get("heart_rate"),
                respiratory_rate=report_data.get("respiratory_rate"),
                blood_pressure_sys=report_data.get("blood_pressure_sys"),
                blood_pressure_dia=report_data.get("blood_pressure_dia"),
                
                # Cardiovascular
                heart_sounds=report_data.get("heart_sounds"),
                pulse_rhythm=report_data.get("pulse_rhythm"),
                pulse_character=report_data.get("pulse_character"),
                
                # Diagnosis
                preliminary_diagnosis=report_data.get("preliminary_diagnosis"),
                final_diagnosis=report_data.get("final_diagnosis"),
                diagnosis_code_icd=report_data.get("diagnosis_code_icd"),
                
                # Exams
                ecg_results=report_data.get("ecg_results"),
                xray_results=report_data.get("xray_results"),
                lab_results=report_data.get("lab_results"),
                other_exams=report_data.get("other_exams"),
                
                # Treatment
                treatment_plan=report_data.get("treatment_plan"),
                prescriptions=report_data.get("prescriptions"),
                procedures=report_data.get("procedures"),
                lifestyle_recommendations=report_data.get("lifestyle_recommendations"),
                diet_recommendations=report_data.get("diet_recommendations"),
                activity_recommendations=report_data.get("activity_recommendations"),
                
                # Conclusions
                doctor_conclusion=report_data.get("doctor_conclusion"),
                prognosis=report_data.get("prognosis"),
                
                # Follow up
                next_visit_date=report_data.get("next_visit_date"),
                next_visit_reason=report_data.get("next_visit_reason"),
                
                # Sick leave
                sick_leave_required=report_data.get("sick_leave_required", False),
                sick_leave_days=report_data.get("sick_leave_days"),
                sick_leave_from=report_data.get("sick_leave_from"),
                sick_leave_to=report_data.get("sick_leave_to"),
            )
            
            report = self._service.create_report(create_dto)
            self.report_created.emit(True, f"Report {report.report_number} created successfully")
            self.load_reports()  # Refresh list
            return report
        
        try:
            return self.safe_execute(_create, "Failed to create report")
        except Exception as e:
            self.report_created.emit(False, str(e))
            return None
    
    def sign_report(self, report_id: int):
        """
        Sign a medical report.
        
        Args:
            report_id: Report to sign
        """
        if not self._service:
            self.report_signed.emit(False, "Service not available")
            return
        
        def _sign():
            # Get doctor info for signature
            doctor_name = self._current_user.full_name
            position = getattr(self._current_user, 'specialization', 'Лікар')
            
            report = self._service.sign_report(report_id, doctor_name, position)
            self.report_signed.emit(True, f"Звіт {report.report_number} успішно підписано")
            self.load_reports()  # Refresh
        
        self.safe_execute(_sign, "Failed to sign report")
    
    def generate_html_report(self, report_id: int, save_path: str = None):
        """
        Generate and optionally save HTML report.
        
        Args:
            report_id: Report ID
            save_path: Optional path to save file
        """
        if not self._service:
            self.report_generated.emit(False, "Service not available", "")
            return
        
        def _generate():
            html = self._service.generate_html_report(report_id)
            
            if save_path:
                filepath = self._service.save_html_report(report_id, html, save_path)
                self.report_generated.emit(
                    True, 
                    f"Report saved to {filepath}", 
                    str(filepath)
                )
            else:
                # Just generate, return HTML content
                self.report_generated.emit(True, "Report generated", html)
        
        self.safe_execute(_generate, "Failed to generate report")
    
    def get_report(self, report_id: int):
        """Get a specific report by ID."""
        if not self._service:
            return None
        return self._service.get_report(report_id)
    
    def delete_report(self, report_id: int):
        """
        Delete a report.
        
        Args:
            report_id: Report to delete
        """
        if not self._service:
            return
        
        def _delete():
            success = self._service.delete_report(report_id, self._current_user.id)
            if success:
                self.load_reports()
            return success
        
        self.safe_execute(_delete, "Failed to delete report")
    
    @property
    def reports(self) -> List[DoctorReportDTO]:
        return self._reports
    
    @property
    def selected_patient_id(self) -> Optional[int]:
        return self._selected_patient_id
