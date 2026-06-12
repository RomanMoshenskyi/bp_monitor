"""Activities ViewModel - for tracking physical activities."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from PyQt6.QtCore import pyqtSignal

from app.presentation.view_models.base_view_model import BaseViewModel
from app.domain.entities import UserORM, ActivityEventORM, ActivityType


class ActivitiesViewModel(BaseViewModel):
    """
    ViewModel for Activities page.
    
    Handles:
    - List of activity events
    - Add new activity
    - Delete activity
    - Link to measurements
    """
    
    # Signals
    activities_changed = pyqtSignal(list)  # List[ActivityEventORM]
    activity_types = pyqtSignal(list)  # List of (value, label) tuples
    
    def __init__(self, current_user: UserORM):
        super().__init__()
        self._current_user = current_user
        self._activities: List[ActivityEventORM] = []
    
    def load_activities(self):
        """Load all activities for current user."""
        def _load():
            self._activities = []
            self.activities_changed.emit(self._activities)
        
        self.safe_execute(_load, "Failed to load activities")
    
    def add_activity(
        self,
        activity_type: str,
        duration_minutes: int,
        intensity: Optional[str] = None,
        calories_burned: Optional[int] = None,
        measurement_id: Optional[int] = None,
        notes: str = ""
    ):
        """Add new activity."""
        def _add():
            # Implementation would use repository
            self.load_activities()
        
        self.safe_execute(_add, "Failed to add activity")
    
    def delete_activity(self, activity_id: int):
        """Delete activity."""
        def _delete():
            # Implementation would use repository
            self.load_activities()
        
        self.safe_execute(_delete, "Failed to delete activity")
    
    def get_activity_types(self) -> List[tuple]:
        """Get list of activity types for dropdown."""
        return [
            ("walking", "Ходьба"),
            ("running", "Біг"),
            ("cycling", "Велосипед"),
            ("swimming", "Плавання"),
            ("gym", "Тренажерний зал"),
            ("yoga", "Йога"),
            ("sport", "Спорт"),
            ("other", "Інше"),
        ]
    
    @property
    def activities(self) -> List[ActivityEventORM]:
        return self._activities
