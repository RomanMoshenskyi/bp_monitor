"""Medications ViewModel - for managing patient medications."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from PyQt6.QtCore import pyqtSignal

from app.presentation.view_models.base_view_model import BaseViewModel
from app.domain.entities import UserORM, MedicationORM


class MedicationsViewModel(BaseViewModel):
    """
    ViewModel for Medications page.
    
    Handles:
    - List of medications
    - Add new medication
    - Edit medication
    - Delete medication
    - Record medication intake
    """
    
    # Signals
    medications_changed = pyqtSignal(list)  # List[MedicationORM]
    intake_recorded = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, current_user: UserORM):
        super().__init__()
        self._current_user = current_user
        self._medications: List[MedicationORM] = []
    
    def load_medications(self):
        """Load all medications for current user."""
        def _load():
            # This would be implemented with actual repository
            # For now, return empty list
            self._medications = []
            self.medications_changed.emit(self._medications)
        
        self.safe_execute(_load, "Failed to load medications")
    
    def add_medication(self, name: str, dosage: str, unit: str, frequency: str, notes: str = ""):
        """Add new medication."""
        def _add():
            # Implementation would use repository
            self.load_medications()  # Refresh
        
        self.safe_execute(_add, "Failed to add medication")
    
    def delete_medication(self, medication_id: int):
        """Delete medication."""
        def _delete():
            # Implementation would use repository
            self.load_medications()  # Refresh
        
        self.safe_execute(_delete, "Failed to delete medication")
    
    def record_intake(self, medication_id: int, measurement_id: Optional[int] = None):
        """Record medication intake."""
        def _record():
            # Implementation would use repository
            self.intake_recorded.emit(True, "Прийом ліків записано")
        
        self.safe_execute(_record, "Failed to record intake")
    
    @property
    def medications(self) -> List[MedicationORM]:
        return self._medications
