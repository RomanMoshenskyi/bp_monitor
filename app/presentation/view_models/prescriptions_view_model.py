"""PrescriptionsViewModel - ViewModel for prescription management."""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
from calendar import monthrange

from PyQt6.QtCore import pyqtSignal, QTimer

from app.presentation.view_models.base_view_model import BaseViewModel
from app.domain.entities import UserORM, UserRole
from app.application.dto import (
    PrescriptionDTO, 
    PrescriptionCreateDTO,
    PrescriptionIntakeDTO,
    CalendarDayDTO,
)
from app.application.services import PrescriptionService


class PrescriptionsViewModel(BaseViewModel):
    """
    ViewModel for Prescriptions and Medication Intake.
    
    Handles:
    - Doctor: Creating prescriptions for patients
    - Patient: Viewing prescriptions and recording intakes
    - Calendar visualization of adherence
    - Reminders for missed intakes
    """
    
    # Signals
    prescriptions_changed = pyqtSignal(list)  # List[PrescriptionDTO]
    prescription_created = pyqtSignal(bool, str)  # success, message
    intakes_changed = pyqtSignal(list)  # List[PrescriptionIntakeDTO]
    intake_recorded = pyqtSignal(bool, str)  # success, message
    calendar_data_changed = pyqtSignal(dict)  # Calendar data
    adherence_stats_changed = pyqtSignal(dict)  # Adherence stats
    missed_intakes_changed = pyqtSignal(list)  # Missed intakes
    pending_intakes_changed = pyqtSignal(list)  # Pending intakes
    
    def __init__(self, current_user: UserORM, db_session=None):
        super().__init__()
        self._current_user = current_user
        self._db_session = db_session
        self._service: Optional[PrescriptionService] = None
        
        # Data storage
        self._prescriptions: List[PrescriptionDTO] = []
        self._intakes: List[PrescriptionIntakeDTO] = []
        self._pending_intakes: List[PrescriptionIntakeDTO] = []
        self._missed_intakes: List[PrescriptionIntakeDTO] = []
        self._calendar_data: Dict[str, Any] = {}
        self._adherence_stats: Dict[str, Any] = {}
        
        # Selected items
        self._selected_patient_id: Optional[int] = None
        self._selected_prescription_id: Optional[int] = None
        
        # Reminder timer
        self._reminder_timer = QTimer()
        self._reminder_timer.timeout.connect(self._check_reminders)
        self._reminder_timer.start(60000)  # Check every minute
        
        if db_session:
            self._service = PrescriptionService(db_session)
            self._load_initial_data()
    
    def set_db_session(self, db_session):
        """Set database session."""
        self._db_session = db_session
        self._service = PrescriptionService(db_session)
        self._load_initial_data()
    
    def _load_initial_data(self):
        """Load initial data based on user role."""
        if self._current_user.role == UserRole.DOCTOR:
            self.load_doctor_prescriptions()
        elif self._current_user.role == UserRole.PATIENT:
            self.load_patient_prescriptions()
            self.load_pending_intakes()
            self.load_missed_intakes()
            self.load_adherence_stats()
    
    # ============== Doctor Methods ==============
    
    def set_selected_patient(self, patient_id: Optional[int]):
        """Set selected patient (for doctor)."""
        self._selected_patient_id = patient_id
    
    def load_doctor_prescriptions(self):
        """Load prescriptions created by current doctor."""
        def _load():
            if not self._service:
                self.prescriptions_changed.emit([])
                return
            
            self._prescriptions = self._service.get_doctor_prescriptions(
                doctor_id=self._current_user.id,
                patient_id=self._selected_patient_id
            )
            self.prescriptions_changed.emit(self._prescriptions)
        
        self.safe_execute(_load, "Failed to load prescriptions")
    
    def get_prescription(self, prescription_id: int):
        """Get a specific prescription by ID."""
        if not self._service:
            return None
        return self._service.get_prescription(prescription_id)
    
    def create_prescription(self, prescription_data: dict):
        """
        Create a new prescription for selected patient.
        
        Args:
            prescription_data: Dictionary with prescription fields
        """
        if not self._service:
            self.prescription_created.emit(False, "Service not available")
            return
        
        if not self._selected_patient_id:
            self.prescription_created.emit(False, "No patient selected")
            return
        
        def _create():
            # Parse specific times
            specific_times = None
            if "specific_times" in prescription_data:
                time_strings = prescription_data["specific_times"]
                if isinstance(time_strings, list):
                    specific_times = []
                    for ts in time_strings:
                        if isinstance(ts, str) and ":" in ts:
                            parts = ts.split(":")
                            specific_times.append(time(int(parts[0]), int(parts[1])))
            
            create_dto = PrescriptionCreateDTO(
                doctor_id=self._current_user.id,
                patient_id=self._selected_patient_id,
                medication_name=prescription_data["medication_name"],
                dosage=prescription_data["dosage"],
                frequency_per_day=prescription_data.get("frequency_per_day", 1),
                medication_form=prescription_data.get("medication_form"),
                specific_times=specific_times,
                duration_days=prescription_data.get("duration_days"),
                start_date=prescription_data.get("start_date", date.today()),
                prescription_date=date.today(),
                take_with_food=prescription_data.get("take_with_food"),
                take_before_food=prescription_data.get("take_before_food"),
                take_after_food=prescription_data.get("take_after_food"),
                special_instructions=prescription_data.get("special_instructions"),
                prescribed_for=prescription_data.get("prescribed_for"),
                contraindications=prescription_data.get("contraindications"),
                side_effects_notes=prescription_data.get("side_effects_notes"),
                interactions_warning=prescription_data.get("interactions_warning"),
            )
            
            prescription = self._service.create_prescription(create_dto)
            self.prescription_created.emit(
                True, 
                f"Prescription {prescription.prescription_number} created for {prescription.medication_name}"
            )
            self.load_doctor_prescriptions()
        
        self.safe_execute(_create, "Failed to create prescription")
    
    def cancel_prescription(self, prescription_id: int, reason: str = None):
        """
        Cancel a prescription.
        
        Args:
            prescription_id: Prescription to cancel
            reason: Cancellation reason
        """
        if not self._service:
            return
        
        def _cancel():
            success = self._service.cancel_prescription(
                prescription_id, 
                self._current_user.id, 
                reason
            )
            if success:
                self.load_doctor_prescriptions()
            return success
        
        self.safe_execute(_cancel, "Failed to cancel prescription")
    
    # ============== Patient Methods ==============
    
    def load_patient_prescriptions(self):
        """Load prescriptions for current patient."""
        def _load():
            if not self._service:
                self.prescriptions_changed.emit([])
                return
            
            self._prescriptions = self._service.get_patient_prescriptions(
                patient_id=self._current_user.id,
                include_completed=False
            )
            self.prescriptions_changed.emit(self._prescriptions)
        
        self.safe_execute(_load, "Failed to load prescriptions")
    
    def accept_prescription(self, prescription_id: int):
        """
        Patient accepts a prescription.
        
        Args:
            prescription_id: Prescription ID
        """
        if not self._service:
            return
        
        def _accept():
            success = self._service.accept_prescription(
                prescription_id, 
                self._current_user.id
            )
            if success:
                self.load_patient_prescriptions()
            return success
        
        self.safe_execute(_accept, "Failed to accept prescription")
    
    def load_pending_intakes(self):
        """Load pending medication intakes."""
        def _load():
            if not self._service:
                self.pending_intakes_changed.emit([])
                return
            
            # Load from now to next 24 hours
            from_time = datetime.utcnow()
            to_time = from_time + __import__('datetime').timedelta(hours=48)
            
            self._pending_intakes = self._service.get_pending_intakes(
                patient_id=self._current_user.id,
                from_time=from_time,
                to_time=to_time
            )
            self.pending_intakes_changed.emit(self._pending_intakes)
        
        self.safe_execute(_load, "Failed to load pending intakes")
    
    def load_missed_intakes(self):
        """Load missed medication intakes."""
        def _load():
            if not self._service:
                self.missed_intakes_changed.emit([])
                return
            
            self._missed_intakes = self._service.get_missed_intakes(
                patient_id=self._current_user.id,
                since=datetime.utcnow() - __import__('datetime').timedelta(days=7)
            )
            self.missed_intakes_changed.emit(self._missed_intakes)
        
        self.safe_execute(_load, "Failed to load missed intakes")
    
    def record_intake(self, intake_id: int, dosage: float = None, notes: str = None):
        """
        Record that medication was taken.
        
        Args:
            intake_id: Intake schedule entry ID
            dosage: Actual dosage taken
            notes: Notes
        """
        if not self._service:
            self.intake_recorded.emit(False, "Service not available")
            return
        
        def _record():
            success = self._service.record_intake(
                intake_id=intake_id,
                patient_id=self._current_user.id,
                taken_at=datetime.now(),  # Use local computer time
                dosage=dosage,
                notes=notes
            )
            if success:
                self.intake_recorded.emit(True, "Intake recorded successfully")
                self.load_pending_intakes()
                self.load_missed_intakes()
                self.load_adherence_stats()
                self.load_calendar_data()
            else:
                self.intake_recorded.emit(False, "Failed to record intake")
        
        self.safe_execute(_record, "Failed to record intake")
    
    def skip_intake(self, intake_id: int, reason: str = None):
        """
        Mark an intake as intentionally skipped.
        
        Args:
            intake_id: Intake schedule entry ID
            reason: Reason for skipping
        """
        if not self._service:
            return
        
        def _skip():
            success = self._service.skip_intake(
                intake_id=intake_id,
                patient_id=self._current_user.id,
                reason=reason
            )
            if success:
                self.load_pending_intakes()
                self.load_missed_intakes()
        
        self.safe_execute(_skip, "Failed to skip intake")
    
    # ============== Calendar & Stats ==============
    
    def load_calendar_data(self, year: int = None, month: int = None):
        """
        Load calendar data for medication adherence.
        
        Args:
            year: Year (defaults to current)
            month: Month (defaults to current)
        """
        def _load():
            nonlocal year, month
            if not self._service:
                self.calendar_data_changed.emit({})
                return
            
            now = datetime.utcnow()
            year = year or now.year
            month = month or now.month
            
            self._calendar_data = self._service.get_intake_calendar_data(
                patient_id=self._current_user.id,
                year=year,
                month=month
            )
            self.calendar_data_changed.emit(self._calendar_data)
        
        self.safe_execute(_load, "Failed to load calendar data")
    
    def load_adherence_stats(self, days: int = 30):
        """
        Load adherence statistics.
        
        Args:
            days: Number of days to analyze
        """
        def _load():
            if not self._service:
                self.adherence_stats_changed.emit({})
                return
            
            self._adherence_stats = self._service.get_adherence_stats(
                patient_id=self._current_user.id,
                days=days
            )
            self.adherence_stats_changed.emit(self._adherence_stats)
        
        self.safe_execute(_load, "Failed to load adherence stats")
    
    def _check_reminders(self):
        """Check for due reminders and auto-mark missed intakes (called by timer)."""
        if not self._service or self._current_user.role != UserRole.PATIENT:
            return
        
        # Auto-mark overdue intakes as missed
        self._service.auto_mark_missed_intakes(self._current_user.id)
        
        # Reload pending intakes to check for overdue
        self.load_pending_intakes()
        
        # Check for overdue intakes and emit signal
        overdue = [
            i for i in self._pending_intakes 
            if i.is_overdue() and i.time_until() < -30  # Overdue by more than 30 min
        ]
        
        if overdue:
            # Emit signal for reminder
            self.missed_intakes_changed.emit(overdue)
    
    def get_upcoming_intakes(self, hours: int = 24) -> List[PrescriptionIntakeDTO]:
        """Get intakes scheduled within the next N hours."""
        now = datetime.utcnow()
        cutoff = now + __import__('datetime').timedelta(hours=hours)
        
        return [
            i for i in self._pending_intakes
            if i.scheduled_time and now <= i.scheduled_time <= cutoff
        ]
    
    # ============== Properties ==============
    
    @property
    def prescriptions(self) -> List[PrescriptionDTO]:
        return self._prescriptions
    
    @property
    def pending_intakes(self) -> List[PrescriptionIntakeDTO]:
        return self._pending_intakes
    
    @property
    def missed_intakes(self) -> List[PrescriptionIntakeDTO]:
        return self._missed_intakes
    
    @property
    def adherence_stats(self) -> Dict[str, Any]:
        return self._adherence_stats
    
    @property
    def calendar_data(self) -> Dict[str, Any]:
        return self._calendar_data
    
    @property
    def is_doctor(self) -> bool:
        return self._current_user.role == UserRole.DOCTOR
    
    @property
    def is_patient(self) -> bool:
        return self._current_user.role == UserRole.PATIENT
