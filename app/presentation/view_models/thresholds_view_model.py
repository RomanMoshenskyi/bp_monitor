"""Thresholds ViewModel - for managing BP threshold profiles."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal

from app.presentation.view_models.base_view_model import BaseViewModel
from app.domain.entities import UserORM, ThresholdProfileORM


class ThresholdsViewModel(BaseViewModel):
    """
    ViewModel for Thresholds page.
    
    Handles:
    - View threshold profile
    - Edit threshold values
    - Check measurement against thresholds
    """
    
    # Signals
    profile_loaded = pyqtSignal(object)  # ThresholdProfileORM or None
    thresholds_saved = pyqtSignal(bool, str)  # success, message
    measurement_checked = pyqtSignal(object)  # dict with status
    
    def __init__(self, current_user: UserORM):
        super().__init__()
        self._current_user = current_user
        self._profile: Optional[ThresholdProfileORM] = None
    
    def load_profile(self):
        """Load threshold profile for current user."""
        def _load():
            # Implementation would use repository
            # For now, create default profile
            self._profile = ThresholdProfileORM(
                patient_id=self._current_user.id,
                sys_min=90,
                sys_max=140,
                dia_min=60,
                dia_max=90,
                pulse_min=50,
                pulse_max=100
            )
            self.profile_loaded.emit(self._profile)
        
        self.safe_execute(_load, "Failed to load threshold profile")
    
    def save_thresholds(
        self,
        sys_min: int,
        sys_max: int,
        dia_min: int,
        dia_max: int,
        pulse_min: Optional[int] = None,
        pulse_max: Optional[int] = None
    ):
        """Save threshold values."""
        def _save():
            # Implementation would use repository
            self.thresholds_saved.emit(True, "Порогові значення збережено")
        
        self.safe_execute(_save, "Failed to save thresholds")
    
    def check_measurement(self, systolic: int, diastolic: int, pulse: Optional[int] = None):
        """Check measurement against thresholds."""
        def _check():
            if self._profile:
                result = self._profile.check_measurement(systolic, diastolic, pulse)
                self.measurement_checked.emit(result)
        
        self.safe_execute(_check, "Failed to check measurement")
    
    @property
    def profile(self) -> Optional[ThresholdProfileORM]:
        return self._profile
