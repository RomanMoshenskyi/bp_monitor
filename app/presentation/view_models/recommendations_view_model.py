"""Recommendations ViewModel - for viewing health recommendations."""
from __future__ import annotations

from typing import List

from PyQt6.QtCore import pyqtSignal

from app.presentation.view_models.base_view_model import BaseViewModel
from app.domain.entities import UserORM, RecommendationORM, SeverityLevel


class RecommendationsViewModel(BaseViewModel):
    """
    ViewModel for Recommendations page.
    
    Handles:
    - List of recommendations
    - Mark as read
    - Acknowledge recommendation
    - Filter by severity
    """
    
    # Signals
    recommendations_changed = pyqtSignal(list)  # List[RecommendationORM]
    unread_count_changed = pyqtSignal(int)
    
    def __init__(self, current_user: UserORM):
        super().__init__()
        self._current_user = current_user
        self._recommendations: List[RecommendationORM] = []
        self._unread_count = 0
    
    def load_recommendations(self, include_read: bool = False):
        """Load recommendations for current user."""
        def _load():
            # Implementation would use repository
            self._recommendations = []
            self.recommendations_changed.emit(self._recommendations)
            self._update_unread_count()
        
        self.safe_execute(_load, "Failed to load recommendations")
    
    def mark_as_read(self, recommendation_id: int):
        """Mark recommendation as read."""
        def _mark():
            # Implementation would use repository
            self.load_recommendations()
        
        self.safe_execute(_mark, "Failed to mark as read")
    
    def acknowledge(self, recommendation_id: int):
        """Acknowledge recommendation (user confirms they understand)."""
        def _ack():
            # Implementation would use repository
            self.load_recommendations()
        
        self.safe_execute(_ack, "Failed to acknowledge")
    
    def _update_unread_count(self):
        """Update unread count."""
        self._unread_count = sum(
            1 for r in self._recommendations 
            if not r.is_read
        )
        self.unread_count_changed.emit(self._unread_count)
    
    def get_severity_options(self) -> List[tuple]:
        """Get severity filter options."""
        return [
            ("all", "Всі"),
            ("low", "Низька"),
            ("medium", "Середня"),
            ("high", "Висока"),
            ("critical", "Критична"),
        ]
    
    @property
    def recommendations(self) -> List[RecommendationORM]:
        return self._recommendations
    
    @property
    def unread_count(self) -> int:
        return self._unread_count
